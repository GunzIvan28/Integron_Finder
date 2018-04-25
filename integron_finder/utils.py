# -*- coding: utf-8 -*-

####################################################################################
# Integron_Finder - Integron Finder aims at detecting integrons in DNA sequences   #
# by finding particular features of the integron:                                  #
#   - the attC sites                                                               #
#   - the integrase                                                                #
#   - and when possible attI site and promoters.                                   #
#                                                                                  #
# Authors: Jean Cury, Bertrand Neron, Eduardo PC Rocha                             #
# Copyright © 2015 - 2018  Institut Pasteur, Paris.                                #
# See the COPYRIGHT file for details                                               #
#                                                                                  #
# integron_finder is free software: you can redistribute it and/or modify          #
# it under the terms of the GNU General Public License as published by             #
# the Free Software Foundation, either version 3 of the License, or                #
# (at your option) any later version.                                              #
#                                                                                  #
# integron_finder is distributed in the hope that it will be useful,               #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                   #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                    #
# GNU General Public License for more details.                                     #
#                                                                                  #
# You should have received a copy of the GNU General Public License                #
# along with this program (COPYING file).                                          #
# If not, see <http://www.gnu.org/licenses/>.                                      #
####################################################################################

import os
from collections import namedtuple

import colorlog
from Bio import Seq
from Bio import SeqIO
import pandas as pd

_log = colorlog.getLogger(__name__)


def make_multi_fasta_reader(alphabet):
    """
    fasta generator maker

    :param alphabet: the alphabet store in the fasta generator closure
    :return: generator to iterate on the fasta file in the same order as in fasta file
    """

    def fasta_iterator(path):
        """
        :param path: The path to the fasta file.
        :return: The sequence parsed.
        :rtype: :class:`Bio.SeqRecord.SeqRecord` object.
        """
        name = get_name_from_path(path)
        seq_it = SeqIO.parse(path, "fasta",  alphabet=alphabet)
        for seq in seq_it:
            seq.name = name
            yield seq

    return fasta_iterator


read_multi_prot_fasta = make_multi_fasta_reader(Seq.IUPAC.protein)


class FastaIterator(object):
    """
    Allow to parse over a multi fasta file, and iterate over it

    .. warning::

        The sequences order is not guarantee.

    """

    def __init__(self, path, alphabet=Seq.IUPAC.unambiguous_dna, replicon_name=None, dist_threshold=4000):
        """

        :param str path: The path to the file containing the sequences.
        :param alphabet: The authorized alphabet
        :type alphabet: Bio.SeqIUPAC member
        :param str replicon_name: The name of the replicon, if this specify all sequence.name will have this value
        :param int dist_threshold: The minimum length for a replicon to be considered as circular.
                                   Under this threshold even the provided topology is 'circular'
                                   the computation will be done with a 'linear' topology.
        """
        self.alphabet = alphabet
        self.seq_index = SeqIO.index(path, "fasta", alphabet=self.alphabet)
        self.seq_gen = (self.seq_index[id_] for id_ in self.seq_index.keys())
        self._topologies = None
        self.replicon_name = replicon_name
        self.dist_threshold = dist_threshold

    def _set_topologies(self, topologies):
        self._topologies = topologies

    topologies = property(fset=_set_topologies)

    def _check_seq_alphabet_compliance(self, seq):
        """
        :param seq: the sequence to check
        :type seq: :class:`Bio.Seq.Seq` instance
        :return: True if sequence letters are a subset of the alphabet, False otherwise.
        """
        seq_letters = set(str(seq).upper())
        alphabet = set(self.alphabet.letters.upper())
        return seq_letters.issubset(alphabet)

    def __next__(self):
        """
        :return: The next sequence (the order of sequences is not guaranteed).
        :rtype: a :class:`Bio.SeqRecord` object or None if the sequence is not compliant with the alphabet.
        """
        try:
            seq = next(self.seq_gen)
        except StopIteration as err:
            self.seq_index.close()
            raise err from None
        if not self._check_seq_alphabet_compliance(seq.seq):
            _log.warning("sequence {} contains invalid characters, the sequence is skipped.".format(seq.id))
            return None
        if len(seq) < 50:
            _log.warning("sequence {} is too short ({} bp), the sequence is skipped (must be > 50bp).".format(seq.id,
                                                                                                              len(seq)))
            return None
        if self.replicon_name is not None:
            seq.name = self.replicon_name
        if self._topologies:
            topology = self._topologies[seq.id]
            # If sequence is too small, it can be problematic when using circularity
            if topology == 'circ' and len(seq) <= 4 * self.dist_threshold:
                topology = 'lin'
            seq.topology = topology
        else:
            seq.topology = 'circ' if len(self) == 1 else 'lin'
        return seq

    def __iter__(self):
        return self


    def __len__(self):
        """:returns: The number of sequence in the file"""
        return len(self.seq_index)


def model_len(path):
    """

    :param str path: the path to the covariance model file
    :return: the length of the model
    :rtype: int
    """
    if not os.path.exists(path):
        msg = "Path to model_attc '{}' does not exists".format(path)
        _log.critical(msg)
        raise IOError(msg)
    with open(path) as model_file:
        for line in model_file:
            if line.startswith('CLEN'):
                model_length = int(line.split()[1])
                return model_length
        msg = "CLEN not found in '{}', maybe it's not infernal model file".format(path)
        _log.critical(msg)
        raise RuntimeError(msg)


def get_name_from_path(path):
    """
    :param path: The path to extract name for instance the fasta file to the replicon
    :return: the name of replicon for instance
             if path = /path/to/replicon.fasta name = replicon
    """
    return os.path.splitext(os.path.split(path)[1])[0]


"""Sequence description with fields: id strand start stop"""
SeqDesc = namedtuple('SeqDesc', ('id', 'strand', 'start', 'stop'))


def gembase_parser(description):
    """
    :param description: description (1rst line without id) of sequence from gembase fasta file
    :return: :class:`SeqDesc` object
    """
    desc = description.split(" ")
    id_, strand, start, stop = desc[:2] + desc[4:6]
    strand = 1 if desc[1] == "D" else -1
    start = int(start)
    stop = int(stop)
    return SeqDesc(id_, strand, start, stop)


def non_gembase_parser(description):
    """
    :param description: description (1rst line without id) of sequence from fasta file not coming a gemabse
    :return: :class:`SeqDesc` object
    """
    id_, start, stop, strand, _ = description.split(" # ")
    start = int(start)
    stop = int(stop)
    strand = int(strand)
    return SeqDesc(id_, strand, start, stop)


def merge_results(*results_file):
    """

    :param results_file: the path of the files (.replicons) to merge.
    :type results_file: str
    :return: all results aggregated in one :class:`pandas.DataFrame` object
    :rtype: a :class:`pandas.DataFrame` object with cols
            "ID_integron", "ID_replicon", "element",
            "pos_beg", "pos_end", "strand", "evalue",
            "type_elt", "annotation", "model",
            "type", "default", "distance_2attC", "considered_topology"
    """
    all_res = []
    for one_result in results_file:
        res = pd.read_table(one_result, sep="\t")
        all_res.append(res)
    agg_results = pd.concat(all_res)
    # agg_results = agg_results.set_index(['ID_replicon', 'ID_integron'])
    # agg_results.drop_duplicates(inplace=True)
    return agg_results


def log_level(verbose, quiet):
        """
        :return: the level to apply to loggers. 0 <= level <=50
        :rtype: int
        """
        default = 20  # info
        level = default - (10 * verbose) + (10 * quiet)
        level = max(10, level)
        level = min(50, level)
        return level
