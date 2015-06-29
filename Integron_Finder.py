#!/usr/bin/env python

"""
integron_finder is a program that looks for integron in DNA sequences.
"""

import numpy as np
import pandas as pd
from Bio import SeqIO
from Bio import motifs
from Bio import Seq
from Bio import SeqFeature
from subprocess import call
import psutil
import os
import argparse
from matplotlib import use as m_use
m_use("Agg")
import matplotlib.pyplot as plt

import distutils.spawn

class Integron:
    """Integron object represents an object composed of an integrase, attC sites and gene cassettes.
    Each element is characterized by their coordinates in the replicon, the strand (+ or -),
    the ID of the gene (except attC).
    The object Integron is also characterized by the ID of the replicon."""

    def __init__(self, ID_replicon): 
        self.ID_replicon = ID_replicon
        self.integrase = pd.DataFrame(columns=["pos_beg", "pos_end", "strand",
                                               "evalue", "type_elt", "model",
                                               "distance_2attC", "annotation"])
        self.attC = pd.DataFrame(columns=["pos_beg", "pos_end", "strand",
                                               "evalue", "type_elt", "model",
                                               "distance_2attC", "annotation"])
        self.promoter = pd.DataFrame(columns=["pos_beg", "pos_end", "strand",
                                               "evalue", "type_elt", "model",
                                               "distance_2attC", "annotation"])
        self.attI = pd.DataFrame(columns=["pos_beg", "pos_end", "strand",
                                               "evalue", "type_elt", "model",
                                               "distance_2attC", "annotation"])
        self.proteins = pd.DataFrame(columns=["pos_beg", "pos_end", "strand",
                                               "evalue", "type_elt", "model",
                                               "distance_2attC", "annotation"])

    def add_integrase(self, pos_beg_int, pos_end_int, id_int, strand_int, evalue, model):
        """Function which adds integrases to the integron. Should be called once"""
        tmp_df = pd.DataFrame()
        tmp_df["pos_beg"] = [pos_beg_int]
        tmp_df["pos_end"] = [pos_end_int]
        tmp_df["strand"] = [strand_int]
        tmp_df["evalue"] = [evalue]
        tmp_df["type_elt"] = "protein"
        tmp_df["annotation"] = "intI"
        tmp_df["model"] = [model]
        tmp_df.index = [id_int]
        tmp_df["distance_2attC"] = [np.nan]
        self.integrase = self.integrase.append(tmp_df)

    def add_attC(self, pos_beg_attC, pos_end_attC, strand, evalue, model):
        """ Function which adds attC site to the Integron object. """
        tmp_df = pd.DataFrame()
        tmp_df["pos_beg"] = [pos_beg_attC]
        tmp_df["pos_end"] = [pos_end_attC]
        tmp_df["strand"] = [strand]
        tmp_df["evalue"] = [evalue]
        tmp_df["type_elt"] = "attC"
        tmp_df["annotation"] = "attC"
        tmp_df["model"] = [model]
        self.attC = self.attC.append(tmp_df, ignore_index=True)
        if len(self.attC) < 2:
            self.sizes_cassettes = [np.nan]
        else:
            self.sizes_cassettes.append((self.attC.iloc[len(self.attC)-1].pos_beg - self.attC.iloc[len(self.attC)-2].pos_end)%SIZE_REPLICON)
        self.attC["distance_2attC"] = self.sizes_cassettes

        #self.attC.sort(["pos_beg"], inplace = True)
        self.attC.index = ["attc_"+"%03i" %int(j+1) for j in self.attC.index]

    def type(self):
        """
        Tells you whether the integrons is :
        - complet : Have one integrase and at least one attC
        - attC0 : Have at least one attC
        - In0 : Just an integrase intI
        """
        
        if len(self.attC) >= 1 and len(self.integrase) >= 1:
            return "complete"
            
        elif len(self.attC) == 0:
            return "In0"
        
        elif len(self.integrase) == 0:
            return "attC0"
    
    def add_promoter(self):
        """
        Function that looks for known promoters if they exists within your integrons element. 
        It takes 1s for about 13kb.
        """
        
        dist_prom = 500 # pb distance from edge of the element for which we seek promoter
        
        ######## Promoter of integrase #########

        if self.has_integrase():

            ## PintI1
            p_intI1 = motifs.create([Seq.Seq("TTGCTGCTTGGATGCCCGAGGCATAGACTGTACA")])         
            p_intI1.name = "P_intI1"

            ## PintI2
            ## Not known
        
            ## PintI3
            ## Not known
        
            motifs_Pint = [p_intI1]
            
            seq_p_int = SEQUENCE.seq[int(self.integrase.pos_beg.min()) - dist_prom : int(self.integrase.pos_end.max()) + dist_prom]        
                        
            for m in motifs_Pint:
                if self.integrase.strand.values[0]==1:    
                    generator_motifs = m.instances.search(seq_p_int[:dist_prom])
                    
                    for pos, s in generator_motifs :
                        tmp_df = pd.DataFrame()            
                        tmp_df["pos_beg"] = [self.integrase.pos_beg.values[0] - dist_prom + pos]
                        tmp_df["pos_end"] = [self.integrase.pos_beg.values[0] - dist_prom + pos + len(s)]
                        tmp_df["strand"] = [self.integrase.strand.values[0]]
                        tmp_df["evalue"] = [np.nan]
                        tmp_df["type_elt"] = "Promoter"
                        tmp_df["annotation"] = "Pint_%s" %(m.name[-1])
                        tmp_df["model"] = "NA"
                        tmp_df.index = [m.name]
                        tmp_df["distance_2attC"] = [np.nan]
                        self.promoter = self.promoter.append(tmp_df)

                else:
                    generator_motifs = m.instances.reverse_complement().search(seq_p_int[-dist_prom:])
                    
                    for pos, s in generator_motifs :
                        tmp_df = pd.DataFrame()            
                        tmp_df["pos_beg"] = [self.integrase.pos_end.max() + pos]
                        tmp_df["pos_end"] = [self.integrase.pos_end.max() + pos + len(s)]
                        tmp_df["strand"] = [self.integrase.strand.values[0]]
                        tmp_df["evalue"] = [np.nan]
                        tmp_df["type_elt"] = "Promoter"
                        tmp_df["annotation"] = "Pint_%s" %(m.name[-1])
                        tmp_df["model"] = "NA"
                        tmp_df.index = [m.name]
                        tmp_df["distance_2attC"] = [np.nan]
                        self.promoter = self.promoter.append(tmp_df)

        ######## Promoter of K7 #########

        ## Pc-int1
        motifs_Pc = []
        
        
        pc = SeqIO.parse(MODEL_DIR + "variants_Pc_intI1.fst", "fasta")
        pseq = [i for i in pc]
        d = {len(i):[] for i in pseq}
        _ = [d[len(i)].append(i.seq.upper()) for i in pseq]
        for k,i in d.iteritems():
            motifs_Pc.append(motifs.create(i))
            motifs_Pc[-1].name = "Pc_int1"
        
        ## Pc-int2
        ## Not known
        
        ## Pc-int3
        
        pc_intI3 = motifs.create([Seq.Seq("TAGACATAAGCTTTCTCGGTCTGTAGGCTGTAATG"),
                                  Seq.Seq("TAGACATAAGCTTTCTCGGTCTGTAGGATGTAATG")])  
        #                                                             *                                         
        pc_intI3.name = "Pc_int3"
        
        motifs_Pc.append(pc_intI3)
        
        if self.type() == "complete":
            
#             if circular:
#                 window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON
#                 window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
#             else:
#                 window_beg = max(0, window_beg - DISTANCE_THRESHOLD)
#                 window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
#                 
                
            if ((self.attC.pos_beg.values[0] - self.integrase.pos_end.values[0] )%SIZE_REPLICON > 
                (self.integrase.pos_beg.values[0] - self.attC.pos_end.values[-1])%SIZE_REPLICON): 
                # if integrase after attcs (on the right)
            
                left = int(self.attC.pos_end.values[-1])
                right = int(self.integrase.pos_beg.values[0])
            
            else:
            
                left = int(self.integrase.pos_end.values[-1])
                right = int(self.attC.pos_beg.values[0])
                
            strand_array = self.attC.strand.unique()[0]
        
        elif self.type() == "In0":
            left = int(self.integrase.pos_beg.values[0])
            right = int(self.integrase.pos_end.values[-1])
            strand_array = "both"
        
        elif self.type() == "attC0":
            left = int(self.attC.pos_beg.values[0])
            right = int(self.attC.pos_end.values[-1])
            strand_array = self.attC.strand.unique()[0]

        if left < right:
            seq_Pc = SEQUENCE.seq[left - dist_prom : right + dist_prom]
        else:
            seq_Pc1 = SEQUENCE.seq[left - dist_prom : SIZE_REPLICON]
            seq_Pc2 = SEQUENCE.seq[:right + dist_prom]
            seq_Pc = seq_Pc1 + seq_Pc2

        for m in motifs_Pc:
        
            if strand_array==1:
                mot = [m]
            elif strand_array=="both":
                mot = [m.reverse_complement(), m]
            else:
                mot = [m.reverse_complement()]
            
            for sa, mo in enumerate(mot):    
                for pos, s in mo.instances.search(seq_Pc):
                    tmp_df = pd.DataFrame()
                    tmp_df["pos_beg"] = [(left - dist_prom + pos)%SIZE_REPLICON]
                    tmp_df["pos_end"] = [(left - dist_prom + pos + len(s))%SIZE_REPLICON]
                    tmp_df["strand"] = [strand_array] if strand_array!="both" else [sa*2-1]
                    tmp_df["evalue"] = [np.nan]
                    tmp_df["type_elt"] = "Promoter"
                    tmp_df["annotation"] = "Pc_%s" %(m.name[-1])
                    tmp_df["model"] = "NA"
                    tmp_df.index = [m.name]
                    tmp_df["distance_2attC"] = [np.nan]
                    self.promoter = self.promoter.append(tmp_df)

    def add_attI(self):
        
        
        dist_atti = 500
        
        ## attI1
        instances_attI1 = [Seq.Seq('TGATGTTATGGAGCAGCAACGATGTTACGCAGCAGGGCAGTCGCCCTAAAACAAAGTT')]                           
        attI1 = motifs.create(instances_attI1) 
        attI1.name = "attI1"
        
        ## attI2
        
        instances_attI2 =  [Seq.Seq('TTAATTAACGGTAAGCATCAGCGGGTGACAAAACGAGCATGCTTACTAATAAAATGTT')]        
        attI2 = motifs.create(instances_attI2) 
        attI2.name = "attI2"
        
        
        ## attI3
        
        instances_attI3 =  [Seq.Seq('CTTTGTTTAACGACCACGGTTGTGGGTATCCGGTGTTTGGTCAGATAAACCACAAGTT')]        
        attI3 = motifs.create(instances_attI3) 
        attI3.name = "attI3"
        
        motif_attI = [attI1, attI2, attI3]
        
        if self.type() == "complete":
 
            if ((self.attC.pos_beg.values[0] - self.integrase.pos_end.values[0] )%SIZE_REPLICON > 
                (self.integrase.pos_beg.values[0] - self.attC.pos_end.values[-1])%SIZE_REPLICON): 
                # if integrase after attcs (on the right)
            
                left = int(self.attC.pos_end.values[-1])
                right = int(self.integrase.pos_beg.values[0]) 
            
            else:
            
                left = int(self.integrase.pos_end.values[-1])
                right = int(self.attC.pos_beg.values[0])
            
            strand_array = self.attC.strand.unique()[0]
        
        elif self.type() == "In0":
            left = int(self.integrase.pos_beg)
            right = int(self.integrase.pos_end)
            strand_array = "both"
        
        elif self.type() == "attC0":
            left = int(self.attC.pos_beg.values[0])
            right = int(self.attC.pos_end.values[-1])
            strand_array = self.attC.strand.unique()[0]
        
        if left < right:
            seq_attI = SEQUENCE.seq[left - dist_atti : right + dist_atti]
        else:
            seq_attI1 = SEQUENCE.seq[left - dist_atti : SIZE_REPLICON]
            seq_attI2 = SEQUENCE.seq[:right + dist_atti]
            seq_attI = seq_attI1 + seq_attI2
        
        for m in motif_attI:
        
            if strand_array==1:
                mot = [m]
            elif strand_array=="both":
                mot = [m.reverse_complement(), m]
            else:
                mot = [m.reverse_complement()]
                
            for sa, mo in enumerate(mot):    
                for pos, s in mo.instances.search(seq_attI):
                    tmp_df = pd.DataFrame()
                    tmp_df["pos_beg"] = [(left - dist_atti + pos)%SIZE_REPLICON]
                    tmp_df["pos_end"] = [(left - dist_atti + pos + len(s))%SIZE_REPLICON]
                    tmp_df["strand"] = [strand_array] if strand_array!="both" else [sa*2-1]
                    tmp_df["evalue"] = [np.nan]
                    tmp_df["type_elt"] = "attI"
                    tmp_df["annotation"] = "attI_%s" %(m.name[-1])
                    tmp_df["model"] = "NA"
                    tmp_df.index = [m.name]
                    tmp_df["distance_2attC"] = [np.nan]
                    self.attI = self.attI.append(tmp_df)
    
    def add_proteins(self):
    
        debut = self.attC.pos_beg.values[0]
        fin   = self.attC.pos_end.values[-1]
        
        if self.has_integrase():

            if ((debut - self.integrase.pos_end.values[0] )%SIZE_REPLICON > 
                (self.integrase.pos_beg.values[0] - fin)%SIZE_REPLICON):
                 # integrase on the right of attC cluster.

                fin = self.integrase.pos_beg.min()
                debut -= 200

            else:

                debut = self.integrase.pos_end.max()
                fin += 200
        else:
            # To allow the first protein after last attC to aggregate.
            debut -= 200
            fin += 200

        if args.resfams:
            resfams_prot = resfams_hits[["ID_prot",
                                         "query_name",
                                         "evalue", "ID_query",
                                       ]].copy().drop_duplicates(subset=["ID_prot"])
                                       
            resfams_prot.set_index("ID_prot", inplace=True)

        for i in SeqIO.parse(PROT_file, "fasta"):    
             
            if not args.gembase:
                desc = [j.strip() for j in i.description.split("#")][:-1]
                start = int(desc[1])
                end = int(desc[2])
                
            else:
                desc = [j for j in i.description.split(" ")]
                desc = desc[:2] + desc[4:6]
                desc[1] = 1 if desc[1] == "D" else -1
                start = int(desc[2])
                end = int(desc[3])
             
            s_int = (fin - debut)%SIZE_REPLICON
            
            if ((  fin - end  )%SIZE_REPLICON < s_int or
                (start - debut)%SIZE_REPLICON < s_int) :
                # We keep proteins (<--->) if start (<) and end (>) follows that scheme:
                # 
                # ok:            <--->         <--->
                # ok:  <--->                                    <--->
                #          ^ 200pb v                    v 200pb ^
                #                  |------integron------|
                #                debut                 fin

                try:
                    prot_annot = resfams_prot.loc[desc[0]].query_name
                    prot_evalue = resfams_prot.loc[desc[0]].evalue
                    prot_model = resfams_prot.loc[desc[0]].ID_query
                except:
                    prot_annot = "protein"
                    prot_evalue = np.nan
                    prot_model = "NA"
                if args.gembase:            
                    self.proteins.loc[desc[0]] = desc[2:] + [desc[1]] + [prot_evalue, "protein", prot_model, np.nan, prot_annot]
                else:
                    self.proteins.loc[desc[0]] = desc[1:] + [prot_evalue, "protein", prot_model, np.nan, prot_annot]
        
    def describe(self):
        """ Method describing the integron object """
    
        full = pd.concat([self.integrase, self.attC, self.promoter, self.attI, self.proteins])
        full["pos_beg"] = full["pos_beg"].astype(int)
        full["pos_end"] = full["pos_end"].astype(int)
        full["strand"] = full["strand"].astype(int)
        full["distance_2attC"] = full["distance_2attC"].astype(float)
        full = full.reset_index()
        full.columns = ["element"] + list(full.columns[1:])
        full["type"] = self.type()
        full["ID_replicon"] = self.ID_replicon
        full["ID_integron"] = id(self) # uniq identifier of a given Integron
        full["default"] = "Yes" if not args.max else "No"
        full.drop_duplicates(subset=["element"], inplace=True)
        return full
        
    def draw_integron(self, file=0):
        """
        Represent the different element of the integrons
        """
        full = self.describe()
        full["evalue"] = full["evalue"].astype("float")
        h = [i + (0.5*i) if j == "Promoter" else i for i,j in zip(full.strand, full.type_elt)]
        fig, ax = plt.subplots(1,1, figsize=(16,9))
        alpha = [i if i<1 else 1 for i in (
                 (np.log10(full.evalue) - np.ones(len(full))*-1)/
                 (np.ones(len(full))*-10 - np.ones(len(full))*-1)
                 *(1 - 0.2)+0.2).fillna(1).tolist()]
                 # normalize alpha value with 0.2 as min value
                 
        colors = ["#749FCD" if i=="attC" else
                  "#DD654B" if i=="intI" else
                  "#6BC865" if i[-2:]=="_1" else
                  "#D06CC0" if i[-2:]=="_2" else
                  "#C3B639" if i[-2:]=="_3" else
                  "#e8950e" if i != "protein" else
                  "#d3d3d3" for i in full.annotation]
        
        colors_alpha = [j+[i] for j,i in zip([[ord(c)/255. for c in i[1:].decode("hex")] for i in colors],
                                              alpha)]          
        
        
        #ec = ["red" if i =="attC" else
        #      "white" for i in full.type_elt]
        z_order = [100 if i =="attC" else
                   1 for i in full.type_elt]

        ax.barh(np.zeros(len(full)), full.pos_end-full.pos_beg,
                 height=h, left=full.pos_beg,
                 color=colors_alpha, zorder=z_order, ec=None) # edgecolor=ec,
        xlims = ax.get_xlim() 
        for c,l in zip(["#749FCD", "#DD654B", "#6BC865", "#D06CC0", "#C3B639", "#e8950e", "#d3d3d3"],
                     ["attC",  "integrase", "Promoter/attI class 1",
                       "Promoter/attI class 2", "Promoter/attI class 3",
                       "ATB resistance", "Hypothetical Protein"]):
            ax.bar(0,0,color=c, label=l)
        plt.legend(loc=[1.01, 0.4])
        ax.set_xlim(xlims)
        fig.subplots_adjust(left=0.05, right=0.80)
        ax.hlines(0, ax.get_xlim()[0], ax.get_xlim()[1], "lightgrey", "--" )
        ax.grid("on", "major", axis="x")    
        ax.set_ylim(-4,4)
        ax.get_yaxis().set_visible(False)
        if file!=0:
            fig.savefig(file, format="pdf")
            plt.close(fig)    
        else:
            fig.show()

    def has_integrase(self):
        if len(self.integrase) >= 1:
            return True
        else:
            return False

    def has_attC(self):
        if len(self.attC) >= 1:
            return True
        else:
            return False


def search_attc(attc_df, replicon, keep_palindromes):
    """
    Parse the attc dataset (sorted along start site) for the given replicon and return list of arrays.
    One array is composed of attC sites on the same strand and separated by a 
    distance less than 5kb
    """
    ok = 0
    
    position_bkp_minus = []
    position_bkp_plus = []
    
    attc_plus  = attc_df[attc_df.sens == "+"].copy()
    attc_minus = attc_df[attc_df.sens == "-"].copy()
        
    if keep_palindromes == False:
        attc_df = attc_df.sort(["pos_beg","evalue"]).drop_duplicates(subset=["pos_beg"]).copy()
        attc_plus  = attc_df[attc_df.sens == "+"].copy()
        attc_minus = attc_df[attc_df.sens == "-"].copy()
    
    # can be reordered
    if (attc_plus.pos_beg.diff() > DISTANCE_THRESHOLD).any() or (attc_minus.pos_beg.diff() > DISTANCE_THRESHOLD).any():
        if len(attc_plus) > 0:
            bkp_plus  = attc_plus[(attc_plus.pos_beg.diff() > DISTANCE_THRESHOLD)].index
            position_bkp_plus = [attc_plus.index.get_loc(i) for i in bkp_plus]
        if len(attc_minus) > 0:
            bkp_minus = attc_minus[(attc_minus.pos_beg.diff() > DISTANCE_THRESHOLD)].index
            position_bkp_minus = [attc_minus.index.get_loc(i) for i in bkp_minus]

        ok = 1
    
    if len(attc_plus) > 0 and len(attc_minus) > 0 :
        ok = 1
    
    if not ok:
        
        if len(attc_df)==0:
            return []
        else:
            
            return [attc_df]
    
    else:
        if len(attc_plus) > 0:
            array_plus = np.split(attc_plus.values, position_bkp_plus)
            if ((array_plus[0][0][4]-array_plus[-1][-1][4])%SIZE_REPLICON < DISTANCE_THRESHOLD and
                len(array_plus) > 1):
                 array_plus[0] = np.concatenate((array_plus[-1], array_plus[0]))
                 del array_plus[-1]

        else:
            array_plus = np.array([])
            
        if len(attc_minus) > 0:
            array_minus = np.split(attc_minus.values, position_bkp_minus)
            if ((array_minus[0][0][4]-array_minus[-1][-1][4])%SIZE_REPLICON < DISTANCE_THRESHOLD and
                len(array_minus) > 1):
                array_minus[0] = np.concatenate((array_minus[-1], array_minus[0]))
                del array_minus[-1]
        else:
            array_minus = np.array([])
        
        
        if len(array_minus) > 0 and len(array_plus) > 0:
            tmp = array_plus + array_minus
        elif len(array_minus) == 0:
            tmp = array_plus
        elif len(array_plus) == 0:
            tmp = array_minus

        attc_array = [pd.DataFrame(i, columns=["Accession_number", "cm_attC", "cm_debut",
                                               "cm_fin", "pos_beg", "pos_end", "sens", "evalue"]) for i in tmp]

        return attc_array

def find_integron(attc_file, intI_file, phage_int_file):
    """ Fonction that looks for integrons given rules :
    - presence of intI
    - presence of attC
    - d(intI-attC) <= 5kb
    - d(attC-attC) <= 5kb
    It returns the list of all integrons, be they complete or not. 
    found in attC files + integrases file which are formatted as follow :
    intI_file :
        Accession_number    ID_prot    strand    pos_beg    pos_end    evalue
    attc_file :
        Accession_number    attC    cm_debut    cm_fin    pos_beg    pos_end    sens    evalue
    """
    intI = read_hmm(intI_file)
    intI.sort(["Accession_number", "pos_beg", "evalue"], inplace=True)

    phageI = read_hmm(phage_int_file)
    phageI.sort(["Accession_number", "pos_beg", "evalue"], inplace=True)

    tmp = intI[intI.ID_prot.isin(phageI.ID_prot)].copy()
    tmp.loc[:,"query_name"] = "intersection_tyr_intI"  

    
    
    if args.union_integrases:
        intI_ac = intI[intI.ID_prot.isin(tmp.ID_prot)==0
                      ].merge(phageI[phageI.ID_prot.isin(tmp.ID_prot)==0],
                              how="outer"
                             ).merge(tmp, how="outer")
    else:   
        intI_ac = tmp

    if isinstance(attc_file, pd.DataFrame):
        attc = attc_file
        attc.sort(["Accession_number","pos_beg", "evalue"], inplace=True)

    else:
        attc = read_infernal(attc_file, evalue = evalue_attc)
        attc.sort(["Accession_number","pos_beg", "evalue"], inplace=True)

    attc_ac = search_attc(attc, name, args.keep_palindromes) # list of Dataframe, each have an array of attC
    integrons = []
    
    
    if len(intI_ac) >= 1 and len(attc_ac) >=1:
        
        n_attc_array = len(attc_ac) # If an array hasn't been clustered with an Integrase
                                    # or if an integrase lacks an array
                                    # redontant info, we could check for len(attc_ac)==0
                                    # -> to remove
        for i,id_int in enumerate(intI_ac.ID_prot.values): #For each Integrase
            
            if n_attc_array == 0: # No more array to attribut to an integrase
                
                integrons.append(Integron(name))
                integrons[-1].add_integrase(intI_ac.pos_beg.values[i],
                                       intI_ac.pos_end.values[i],
                                       id_int,
                                       int(intI_ac.strand.values[i]),
                                       intI_ac.evalue.values[i],
                                       intI_ac.query_name.values[i])

            else: # we still have attC and int :
                attc_left = np.array([i_attc.pos_beg.values[0] for i_attc in attc_ac])
                attc_right = np.array([i_attc.pos_end.values[-1] for i_attc in attc_ac])
                
                distances = np.array([(attc_left - intI_ac.pos_end.values[i] ),
                                      (intI_ac.pos_beg.values[i] - attc_right)])%SIZE_REPLICON
                
                
                if len(attc_ac)>1:
                    #tmp = (distances /
                    #       np.array([[len(aac) for aac in attc_ac]]))
                           
                    side, idx_attc = np.where((distances)==(distances).min())
                    # side : 0 <=> left; 1 <=> right
                    # index of the closest and biggest attC array to the integrase
                    # exactly tmp = dist(cluster to integrase) / size cluster 
                    # to make a decision between 2 equally distant arrays
                    # Usually they are on the same side but on 2 different strands
                    
                    # If they are exactly similare (same distance, same number of attC, take the first one arbitrarly
                    # Or just flatten from idx_attc=[i] to idx_attc=i
                    idx_attc = idx_attc[0]
                    side = side[0]
                
                else:
                    idx_attc = 0
                    side = np.argmin(distances)

                if distances[side, idx_attc] < DISTANCE_THRESHOLD:

                    integrons.append(Integron(name))
                    integrons[-1].add_integrase(intI_ac.pos_beg.values[i],
                                                intI_ac.pos_end.values[i],
                                                id_int,
                                                int(intI_ac.strand.values[i]),
                                                intI_ac.evalue.values[i],
                                                intI_ac.query_name.values[i])
                   
                    attc_tmp = attc_ac.pop(idx_attc)
                    
                    for a_tmp in attc_tmp.values:
                        integrons[-1].add_attC(a_tmp[4],
                                               a_tmp[5],
                                               1 if a_tmp[6]=="+" else -1,
                                               a_tmp[7], model_attc_name)
                    n_attc_array -= 1  
                
                
                else: # no array close to the integrase on both side

                    integrons.append(Integron(name))
                    integrons[-1].add_integrase(intI_ac.pos_beg.values[i],
                                                intI_ac.pos_end.values[i],
                                                id_int,
                                                int(intI_ac.strand.values[i]),
                                                intI_ac.evalue.values[i], intI_ac.query_name.values[i])


        if n_attc_array > 0: # after the integrase loop (<=> no more integrases)

            for attc_array in attc_ac: 
                integrons.append(Integron(name))

                for a_tmp in attc_array.values:
                    integrons[-1].add_attC(a_tmp[4],
                                           a_tmp[5],
                                           1 if a_tmp[6]=="+" else -1,
                                           a_tmp[7], model_attc_name)
            

    elif  len(intI_ac.pos_end.values) == 0 and len(attc_ac) >=1 : # Si attC seulement

        for attc_array in attc_ac:
            integrons.append(Integron(name))
            
            for a_tmp in attc_array.values:
                integrons[-1].add_attC(a_tmp[4],
                                              a_tmp[5],
                                              1 if a_tmp[6]=="+" else -1,
                                              a_tmp[7], model_attc_name)
            
        
        
    elif  len(intI_ac.pos_end.values) >= 1 and len(attc_ac) == 0: # Si intI seulement

        for i,id_int in enumerate(intI_ac.ID_prot.values):
            integrons.append(Integron(name))
            integrons[-1].add_integrase(intI_ac.pos_beg.values[i],
                                       intI_ac.pos_end.values[i],
                                       id_int,
                                       int(intI_ac.strand.values[i]),
                                       intI_ac.evalue.values[i],
                                       intI_ac.query_name.values[i])

    print "In replicon {}, there are:".format(name)
    print "- {} complete integron(s) found with {} attC site(s)".format(sum([1 if i.type()=="complete" else 0 for i in integrons]),
                                                                  sum([len(i.attC) if i.type()=="complete" else 0 for i in integrons]))
    print "- {} attC0 integron(s) found with {} attC site(s)".format(sum([1 if i.type()=="attC0" else 0 for i in integrons]),
                                                               sum([len(i.attC) if i.type()=="attC0" else 0 for i in integrons]))                
    print "- {} In0 integron(s) found with {} attC site".format(sum([1 if i.type()=="In0" else 0 for i in integrons]),
                                                             sum([len(i.attC) if i.type()=="In0" else 0 for i in integrons]))                

    return integrons


def expand(window_beg, window_end, max_elt, df_max, search_left=False, search_right=False):
    

    # for a given element, we can search on the left hand side (if integrase is on the right for instance)
    # or right hand side (opposite situation) or both side (only integrase or only attC sites)
    wb = window_beg
    we = window_end
    if search_right:    
        
        if circular:
            window_beg = (window_end - 200)%SIZE_REPLICON # 200 to allow the detection of sites that would overlap 2 consecutive windows
            window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
        else:
            window_beg = max(0, window_end - 200) # 200 to allow the detection of sites that would overlap 2 consecutive windows
            window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
        
        searched_strand = "both" if search_left else "top" # search on both strands if search in both directions
        
        while len(df_max) > 0 and 0 < (window_beg and window_end) < SIZE_REPLICON:
            
            df_max = local_max(window_beg, window_end, searched_strand)
            max_elt = pd.concat([max_elt, df_max])
            
            if circular:
                window_beg = (window_end - 200)%SIZE_REPLICON 
                window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
            else:
                window_beg = max(0, window_end - 200)
                window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
            
        # re-initialize in case we enter search left too.
        df_max = max_elt.copy()
        window_beg = wb 
        window_end = we



    if search_left:
        if circular:
            window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON 
            window_end = (window_beg + 200)%SIZE_REPLICON
        else:
            window_beg = max(0, window_beg - DISTANCE_THRESHOLD) 
            window_end = min(SIZE_REPLICON, window_beg + 200)
            
        searched_strand = "both" if search_right else "bottom"
        
        while len(df_max) > 0 and 0 < (window_beg and window_end) < SIZE_REPLICON:
                        
            df_max = local_max(window_beg, window_end, searched_strand)
            max_elt = pd.concat([max_elt, df_max]) #update of attC list of hits.
            
            if circular:
                window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON 
                window_end = (window_beg + 200)%SIZE_REPLICON
            else:
                window_beg = max(0, window_beg - DISTANCE_THRESHOLD) 
                window_end = min(SIZE_REPLICON, window_beg + 200)
        
            
    max_elt.drop_duplicates(inplace=True)
    max_elt.index = range(len(max_elt))
    return max_elt


def find_attc_max(integrons, name, in_dir, outfile="attC_max_1.res"):
    """
    Look for attC site with cmsearch --max option wich remove all heuristic filters. 
    As this option make the algorithm way slower, we only run it in the region around a
    hit.
    
    integrons is a list of Integron object, they may have or not attC or intI.
    
    Default hit :
    =============
                     attC
    __________________-->____-->_________-->_____________
    ______<--------______________________________________
             intI
                  ^-------------------------------------^
                 Search-space with --max 
    
    Updated hit :
    =============
    
                     attC          ***         ***
    __________________-->____-->___-->___-->___-->_______
    ______<--------______________________________________
             intI
        
    """
    

        
    max_final = pd.DataFrame(columns=['Accession_number', 'cm_attC', 'cm_debut', 'cm_fin',
                                      'pos_beg', 'pos_end', 'sens', 'evalue'])
    for i in integrons:
        
        max_elt = pd.DataFrame(columns=['Accession_number', 'cm_attC', 'cm_debut', 'cm_fin',
                                        'pos_beg', 'pos_end', 'sens', 'evalue'])
        full_element = i.describe()
        
        if all(full_element.type == "complete"):
            
            window_beg = full_element[full_element.type_elt=="attC"].pos_beg.values[0]
            window_end = full_element[full_element.type_elt=="attC"].pos_end.values[-1]
            
            if circular:
                window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON
                window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
            else:
                window_beg = max(0, window_beg - DISTANCE_THRESHOLD)
                window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
                
            strand = "top" if full_element[full_element.type_elt=="attC"].strand.values[0] == 1 else "bottom"

            df_max = local_max(window_beg, window_end, strand) 
            
            max_elt = pd.concat([max_elt, df_max])
                            
            # Where is the integrase compared to the attc sites (no matter the strand) :
            integrase_is_left = ((full_element[full_element.type_elt=="attC"].pos_beg.values[0] -
                                  full_element[full_element.annotation=="intI"
                                               ].pos_end.values[0])%SIZE_REPLICON <
                                 (full_element[full_element.annotation=="intI"
                                               ].pos_beg.values[0] - 
                                  full_element[full_element.type_elt=="attC"].pos_end.values[-1])%SIZE_REPLICON)
            
            
            # If we find new attC after the last found with default algo and if the integrase is on the left 
            # (We don't expand over the integrase) :
                        
            go_left = (full_element[full_element.type_elt=="attC"].pos_beg.values[0] - df_max.pos_end.values[-1] 
                       )%SIZE_REPLICON < DISTANCE_THRESHOLD and not integrase_is_left
                       
            go_right = (df_max.pos_beg.values[0] - full_element[full_element.type_elt=="attC"].pos_end.values[-1] 
                        )%SIZE_REPLICON < DISTANCE_THRESHOLD and integrase_is_left

            max_elt = expand(window_beg, window_end, max_elt, df_max,
                             search_left=go_left, search_right=go_right)

            
        elif all(full_element.type == "attC0"):
            
            if len(full_element[full_element.pos_beg.isin(max_final.pos_beg)]) == 0: # if cluster don't overlap already max-searched region 
                
                window_beg = full_element[full_element.type_elt=="attC"].pos_beg.values[0]
                window_end = full_element[full_element.type_elt=="attC"].pos_end.values[-1]

                if circular:
                    window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON
                    window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
                else:
                    window_beg = max(0, window_beg - DISTANCE_THRESHOLD)
                    window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
                    
                strand = "top" if full_element[full_element.type_elt=="attC"].strand.values[0] == 1 else "bottom"

                df_max = local_max(window_beg, window_end, strand)

                max_elt = pd.concat([max_elt, df_max])

                if len(df_max) > 0: # Max can sometimes find bigger attC than permitted
                    go_left = (full_element[full_element.type_elt=="attC"].pos_beg.values[0] - df_max.pos_end.values[-1] 
                               )%SIZE_REPLICON < DISTANCE_THRESHOLD 
                       
                    go_right = (df_max.pos_beg.values[0] - full_element[full_element.type_elt=="attC"].pos_end.values[-1] 
                                )%SIZE_REPLICON < DISTANCE_THRESHOLD 

                    max_elt = expand(window_beg, window_end, max_elt, df_max,
                                     search_left=go_left, search_right=go_right)
        
        elif all(full_element.type == "In0"):

            if all(full_element.model != "Phage_integrase"):
            
                window_beg = full_element[full_element.annotation=="intI"].pos_beg.values[0]
                window_end = full_element[full_element.annotation=="intI"].pos_end.values[-1]

                if circular:
                    window_beg = (window_beg - DISTANCE_THRESHOLD)%SIZE_REPLICON
                    window_end = (window_end + DISTANCE_THRESHOLD)%SIZE_REPLICON
                else:
                    window_beg = max(0, window_beg - DISTANCE_THRESHOLD)
                    window_end = min(SIZE_REPLICON, window_end + DISTANCE_THRESHOLD)
            
                df_max = local_max(window_beg, window_end)
            
                max_elt = pd.concat([max_elt, df_max])
            
                if len(max_elt) > 0:
                
                    max_elt = expand(window_beg, window_end, max_elt, df_max,
                                     search_left=True, search_right=True)
        
                
        
        max_final = pd.concat([max_final, max_elt])
        max_final.drop_duplicates(subset=max_final.columns[:-1], inplace=True)
        
        max_final.index = range(len(max_final))
        
    return max_final


def local_max(window_beg, window_end, strand_search="both"):


    if window_beg < window_end:
        subseq = SEQUENCE[window_beg : window_end]
    else:
        subseq1 = SEQUENCE[window_beg : SIZE_REPLICON]
        subseq2 = SEQUENCE[:window_end]
        subseq = subseq1 + subseq2
    
    with open(out_dir + name + "_subseq.fst", "w") as f:
        SeqIO.write(subseq, f, "fasta")
    
    if strand_search == "both" :
        call([CMSEARCH, "-Z", str(SIZE_REPLICON/1000000.), "--max",
              "--cpu", N_CPU, "-o",
              out_dir + name + "_" + str(window_beg) + "_" + str(window_end) + "_subseq_attc.res",
              "--tblout", out_dir + name + "_subseq_attc_table.res", "-E" "10",
              MODEL_attc, out_dir + name + "_subseq.fst"])
    
    elif strand_search == "top":
        call([CMSEARCH, "-Z", str(SIZE_REPLICON/1000000.), "--toponly",
              "--max", "--cpu", N_CPU, "-o",
              out_dir + name + "_" + str(window_beg) + "_" + str(window_end) + "_subseq_attc.res",
              "--tblout", out_dir + name  + "_subseq_attc_table.res", "-E" "10",
              MODEL_attc, out_dir + name + "_subseq.fst"])
    
    elif strand_search == "bottom":
        call([CMSEARCH, "-Z", str(SIZE_REPLICON/1000000.), "--bottomonly",
              "--max", "--cpu", N_CPU, "-o",
              out_dir + name + "_" + str(window_beg) + "_" + str(window_end) + "_subseq_attc.res",
              "--tblout", out_dir + name + "_subseq_attc_table.res", "-E" "10",
              MODEL_attc, out_dir + name + "_subseq.fst"])
    
    df_max = read_infernal(out_dir + name + "_subseq_attc_table.res", evalue = evalue_attc)
    df_max.pos_beg = (df_max.pos_beg + window_beg)%SIZE_REPLICON
    df_max.pos_end = (df_max.pos_end + window_beg)%SIZE_REPLICON
    df_max.to_csv(out_dir + name + "_" + "subseq_attc_table_end.res", sep="\t", index=0, mode="a", header=0)
    df_max = df_max[(abs(df_max.pos_end - df_max.pos_beg)>40) & (abs(df_max.pos_end - df_max.pos_beg)<200)] # filter on size
    #print df_max
    
    return df_max

def find_attc(name, in_dir = ".", out_dir = "."):
    """
    Call cmsearch to find attC site in a single replicon.
    Return nothing, the results are written on the disk
    """      
    call([CMSEARCH, "--cpu", N_CPU, "-o", out_dir + name + "_attc.res",
          "--tblout", out_dir + name + "_attc_table.res", "-E" "10",
          MODEL_attc, os.path.abspath(in_dir + name + ".fst")])

def find_integrase(name, in_dir = ".", out_dir = "."):
    """
    Call Prodigal for Gene annotation and hmmer to find integrase, either with phage_int
    HMM profile or with intI profile.
    
    replicon is the in_dir to the replicon file, or just the file if in current dir.
    
    Return nothing, the results are written on the disk
    """
    
    if not args.gembase:
        # Test whether the protein file exist to avoid new annotation for each run on the same replicon
        if os.path.isfile(out_dir + "/" + name + ".prt") == False:
            if SIZE_REPLICON > 200000:

                call([PRODIGAL, "-i",  in_dir + name + ".fst",
                      "-a", out_dir + "/" + name + ".prt", "-o", "/dev/null"])

            else: # if small genome, prodigal annotate it as contig.
                call([PRODIGAL, "-p", "meta", "-i",  in_dir + name + ".fst",
                      "-a", out_dir + "/" + name + ".prt", "-o", "/dev/null"])
    
    if os.path.isfile(out_dir + name + "_intI_table.res") == False:
                    
        call([HMMSEARCH, "--cpu", N_CPU, "--tblout", out_dir + name + "_intI_table.res",
              "-o", out_dir + name + "_intI.res", MODEL_integrase,
              PROT_file])
    if os.path.isfile(out_dir + name + "_phage_int_table.res") == False:
        call([HMMSEARCH, "--cpu", N_CPU, "--tblout",
              out_dir + name + "_phage_int_table.res",
              "-o", out_dir + name + "_phage_int.res", MODEL_phage_int,
              PROT_file])
    

def find_resfams(name, in_dir=".", out_dir=".", evalue=10,  hmm_file="Resfams.hmm"):
    """
    Call hmmmer to annotate antibiotique resistance gene with the model from Resfams (Gibson et al, ISME J.,  2014)
    """
    call([HMMSEARCH, "--cpu", N_CPU, "--tblout", out_dir + name + "_atb_table.res",
          "-o", out_dir + name + "_atb.res", MODEL_DIR + hmm_file,
          PROT_file])

def read_hmm(infile, evalue=1):
    """
    Function that parse hmmer --tblout output and returns a pandas DataFrame
    """
    try:
        _ = pd.read_table(infile, comment="#")
    except:
        return pd.DataFrame(columns = ["Accession_number","query_name", "ID_query", "ID_prot","strand","pos_beg","pos_end","evalue"])
        
    if not args.gembase:
        df = pd.read_table(infile, sep="\s*", engine="python", header=None, skipfooter=10, skiprows=3)
        df = df[[2,3,0,23,19,21,4]]
        df = df[df[4] < evalue]
        df["Accession_number"] = name
        c = df.columns.tolist()
        df = df[c[-1:] + c[:-1]]
        df.sort([19,4], inplace=True)
        df.index = range(0,len(df))
        df.columns = ["Accession_number","query_name", "ID_query", "ID_prot","strand","pos_beg","pos_end","evalue"]
        return df
    else:
        df_tmp = pd.read_table(infile, sep="|", engine="python", header=None, skipfooter=10, skiprows=3)
        df = pd.DataFrame(df_tmp[0].str.split().tolist())
        df = df[[2,3,0,18,21,22,4]]
        df[[21,22,4]] = df[[21,22,4]].astype("float")
        df = df[df[4] < evalue]
        df["Accession_number"] = name
        c = df.columns.tolist()
        df = df[c[-1:] + c[:-1]]
        df.sort([21,4], inplace=True)
        df.index = range(0,len(df))
        df.columns = ["Accession_number","query_name", "ID_query", "ID_prot","strand","pos_beg","pos_end","evalue"]
        df["strand"] = df["strand"].apply(lambda x: 1 if x =="D" else -1)
        return df

def read_infernal(infile, evalue=1, size_max_attc=200, size_min_attc=40):
    """
    Function that parse cmsearch --tblout output and returns a pandas DataFrame
    """
   
    try:
        _ = pd.read_table(infile, comment="#")
    except:
        return pd.DataFrame(columns = ["Accession_number","cm_attC","cm_debut","cm_fin","pos_beg","pos_end","sens","evalue"])
    
    df = pd.read_table(infile, sep="\s*", engine="python",
                       header=None, skipfooter=10, skiprows=2)
    df = df[[2,5,6,7,8,9,15]]
    df = df[(df[15] < evalue)]
    df = df[(abs(df[8]-df[7]) < size_max_attc) & (size_min_attc < abs(df[8]-df[7]))] # filter on evalue
    df["Accession_number"] = name
    c = df.columns.tolist()
    df = df[c[-1:] + c[:-1]]
    df.sort([8,15], inplace=True)
    df.index = range(0,len(df))
    df.columns = ["Accession_number", "cm_attC", "cm_debut", "cm_fin",
                  "pos_beg", "pos_end",
                  "sens", "evalue"]
    idx = (df.pos_beg > df.pos_end)
    df.loc[idx, ['pos_beg', 'pos_end']] = df.loc[idx, ['pos_end','pos_beg']].values  
    return df

def to_gbk(df, sequence):

    """ from a dataframe like integrons_describe and a sequence, create an genbank file with integron annotation """
    
    df = df.set_index("ID_integron").copy()
    for i in df.index.unique():

        if isinstance(df.loc[i], pd.Series):
            type_integron = df.loc[i].type
            start_integron = df.loc[i].pos_beg
            end_integron = df.loc[i].pos_end
            tmp = SeqFeature.SeqFeature(location=
               SeqFeature.FeatureLocation(start_integron-1,
                                         end_integron),
               strand=0,
               type="integron",
               qualifiers={"integron_id" : i,
                           "integron_type" : type_integron}
               )
            sequence.features.append(tmp)    
            if (df.loc[i].type_elt=="protein"):
        
                tmp = SeqFeature.SeqFeature(location=
                                       SeqFeature.FeatureLocation(df.loc[i].pos_beg-1,
                                                                 df.loc[i].pos_end),
                                       strand=df.loc[i].strand,
                                       type="CDS" if df.loc[i].annotation != "intI" else "integrase",
                                       qualifiers={"protein_id" : df.loc[i].element,
                                                  "gene" : df.loc[i].annotation,
                                                  "model" : df.loc[i].model}
                                       )           
    
                tmp.qualifiers["translation"] = [prt for prt in SeqIO.parse(PROT_file,
                                                                        "fasta")
                                                 if prt.id == df.loc[i].element][0].seq
                sequence.features.append(tmp)
            
                
            else:
                tmp = SeqFeature.SeqFeature(location=
                                   SeqFeature.FeatureLocation(df.loc[i].pos_beg-1,
                                                             df.loc[i].pos_end),
                                   strand=df.loc[i].strand,
                                   type=df.loc[i].type_elt,
                                   qualifiers={df.loc[i].type_elt :df.loc[i].element,
                                               "model" : df.loc[i].model}
                                   )

                sequence.features.append(tmp)       
                
        else:
            type_integron = df.loc[i].type.values[0]
            # Should only be true if integron over edge of sequence:
            diff = df.loc[i].pos_beg.diff() > DISTANCE_THRESHOLD
            
            if diff.any():
                pos = np.where(diff)[0][0]

                start_integron_1 =  df.loc[i].pos_beg.values[pos]
                
                end_integron_1 = SIZE_REPLICON

                start_integron_2 = 1            

                end_integron_2 =  df.loc[i].pos_end.values[pos-1]
                
                f1 = SeqFeature.FeatureLocation(start_integron_1-1, end_integron_1)
                f2 = SeqFeature.FeatureLocation(start_integron_2-1, end_integron_2)
                tmp = SeqFeature.SeqFeature(location=f1+f2,
                               strand=0,
                               type="integron",
                               qualifiers={"integron_id" : i,
                                           "integron_type" : type_integron}
                               )
                
                
            else:
                
                start_integron = df.loc[i].pos_beg.values[0]
                end_integron = df.loc[i].pos_end.values[-1]
                
                tmp = SeqFeature.SeqFeature(location=
                               SeqFeature.FeatureLocation(start_integron-1,
                                                         end_integron),
                               strand=0,
                               type="integron",
                               qualifiers={"integron_id" : i,
                                           "integron_type" : type_integron}
                               )
            sequence.features.append(tmp)      
            for r in df.loc[i].iterrows():
                
                if (r[1].type_elt=="protein"):
                    tmp = SeqFeature.SeqFeature(location=
                                           SeqFeature.FeatureLocation(r[1].pos_beg-1,
                                                                     r[1].pos_end),
                                           strand=r[1].strand,
                                           type="CDS" if r[1].annotation != "intI" else "integrase",
                                           qualifiers={"protein_id" : r[1].element,
                                                      "gene" : r[1].annotation,
                                                      "model" : r[1].model}
                                           )           
    
                    tmp.qualifiers["translation"] = [prt for prt in SeqIO.parse(PROT_file,
                                                                            "fasta")
                                                     if prt.id == r[1].element][0].seq
            
                    sequence.features.append(tmp)
                else:
                    tmp = SeqFeature.SeqFeature(location=
                                       SeqFeature.FeatureLocation(r[1].pos_beg-1,
                                                                 r[1].pos_end),
                                       strand=r[1].strand,
                                       type=r[1].type_elt,
                                       qualifiers={r[1].type_elt :r[1].element,
                                                   "model" : r[1].model}
                                   )           


                    sequence.features.append(tmp)

        

if __name__ == "__main__":


    ############### Arguments and declarations ###############
    
    parser = argparse.ArgumentParser()
    parser.add_argument("replicon", help="Path and/or fasta file to the replicon, eg : path/to/file.fst or file.fst")
    parser.add_argument("--max", help="Allows exact local detection (slower)",
                    action="store_true")
    parser.add_argument("--resfams", help="Detect antibiotic resistances with Resfams HMM profiles",
                    action="store_true")

    parser.add_argument('--cpu',
                    default='1',
                    action='store',
                    type=str,
                    help='Number of CPUs used by INFERNAL and HMMER')
                    
    parser.add_argument('-dt', '--distance_thresh',
                    default=4000,
                    action='store',
                    type=int,
                    help='Two element are aggregated if they are distant of DISTANCE_THRESH [4kb] or less')
                    
                    
    parser.add_argument('--outdir',
                    default=".",
                    action='store',
                    type=str,
                    metavar='.',
                    help='set the output directory (default: current)')
    
    parser.add_argument("--linear", help="consider replicon as linear. If replicon smaller than 20kb, it will be considered as linear",
                        action="store_true")                        
    
    parser.add_argument("--union_integrases", help="Instead of taking intersection of hits from Phage_int profile (Tyr recombinases) and integron_integrase profile, use the union of the hits",
                    action="store_true")

    parser.add_argument('--cmsearch',
                    default=distutils.spawn.find_executable("cmsearch"),
                    action='store',
                    type=str,
                    help='Complete path to cmsearch if not in PATH. eg: /usr/local/bin/cmsearch')

    parser.add_argument('--hmmsearch',
                    default=distutils.spawn.find_executable("hmmsearch"),
                    action='store',
                    type=str,
                    help='Complete path to hmmsearch if not in PATH. eg: /usr/local/bin/hmmsearch')

    parser.add_argument('--prodigal',
                    default=distutils.spawn.find_executable("prodigal"),
                    action='store',
                    type=str,
                    help='Complete path to prodigal if not in PATH. eg: /usr/local/bin/prodigal')
   
    parser.add_argument("--gembase", help="Use gembase formatted protein file instead of Prodigal. Folder structure must be preserved",
                    action="store_true")
                    
    
    parser.add_argument('--attc_model',
                    default='attc_4.cm',
                    action='store',
                    type=str,
                    metavar='file.cm',
                    help='path or file to the attc model (Covariance Matrix)')
                    
    parser.add_argument('--evalue_attc',
                    default=1.,
                    action='store',
                    type=float,
                    metavar='1',
                    help='set evalue threshold to filter out hits above it (default: 1)')

    parser.add_argument("--keep_palindromes", help="for a given hit, if the palindromic version is found, don't remove the one with highest evalue ",
                        action="store_true")
                        
        
    args = parser.parse_args()
    replicon = args.replicon    
    evalue_attc = args.evalue_attc
    
    name = ".".join(replicon.split("/")[-1].split(".")[:-1])
    extension = replicon.split("/")[-1].split(".")[-1]
    mode_name = "max" if args.max else "default"
    
    try:
        os.mkdir(args.outdir)
    except OSError:
        pass
        
    try:
        os.mkdir(args.outdir + "/Results_Integron_Finder_" + name + "/")
    except OSError:
        pass
    
    
    out_dir = args.outdir + "/Results_Integron_Finder_" + name + "/"

    if len(replicon.split("/")) > 1:
        in_dir = "/".join(replicon.split("/")[:-1]) + "/"
    else:
        in_dir = "./"

    SEQUENCE = SeqIO.read(in_dir + "/" + name + "." + extension, "fasta",
                          alphabet = Seq.IUPAC.unambiguous_dna)
    
    
    ############### Definitions ###############
    
    N_CPU = args.cpu
    SIZE_REPLICON = len(SEQUENCE)
    DISTANCE_THRESHOLD = args.distance_thresh
    
    # If sequence is too small, it can be problematic when using circularity
    if len(SEQUENCE) > 4 * DISTANCE_THRESHOLD:
        circular = not args.linear
    else:
        circular = False

    MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Models")
    MODEL_integrase = os.path.join(MODEL_DIR, "integron_integrase.hmm")
    MODEL_phage_int = os.path.join(MODEL_DIR, "phage-int.hmm")

    CMSEARCH = args.cmsearch
    HMMSEARCH = args.hmmsearch
    PRODIGAL = args.prodigal

    RESFAMS_HMM = "Resfams.hmm"
    
    if len(args.attc_model.split("/")) > 1: #contain path
        MODEL_attc = args.attc_model
    else:
        MODEL_attc = os.path.join(MODEL_DIR, args.attc_model)

    model_attc_name = MODEL_attc.split("/")[-1].split(".cm")[0]
    
    if args.gembase:
        PROT_dir = os.path.jon(in_dir, "..", "Proteins")
        PROT_file = os.path.join(PROT_dir, name + ".prt")
    else:
        PROT_file = os.path.join(out_dir, name + ".prt")

    ############### Default search ###############

    find_attc(name, in_dir, out_dir)
    find_integrase(name, in_dir, out_dir)    

    print "Default search done... : \n"
    integrons = find_integron(out_dir + name + "_attc_table.res", 
                              out_dir + name + "_intI_table.res", 
                              out_dir + name + "_phage_int_table.res")
    if args.resfams:
        
        if not os.path.isfile(os,path.join(out_dir, "/", name + "_atb_table.res")):
            find_resfams(name, in_dir, out_dir, RESFAMS_HMM)
        
        resfams_hits = read_hmm(out_dir + name + "_atb_table.res")
        
    ############### Max search ###############
    if args.max:
        integron_max = find_attc_max(integrons, name, in_dir)

        print "Max search done... : \n"

        integrons = find_integron(integron_max,
                                  out_dir + name + "_intI_table.res",
                                  out_dir + name + "_phage_int_table.res")


    ############### Writing out results ###############

    outfile = name + ".integrons"

    if len(integrons):
        j = 1
        for i in integrons:
            if i.type() != "In0": # complete & attC0
                i.add_proteins()
                
            if i.type() == "complete":
                i.add_promoter()
                i.add_attI()
                i.draw_integron(file=out_dir + name + "_" + str(j) + ".pdf")
                j += 1
            if i.type() == "In0":
                i.add_attI()
                i.add_promoter()

        
        integrons_describe = pd.concat([i.describe() for i in integrons])
        dic_id = {i:"%02i" %(j+1) for j,i in enumerate(integrons_describe.sort("pos_beg").ID_integron.unique())}
        integrons_describe.ID_integron = ["integron_"+dic_id[i] for i in integrons_describe.ID_integron]
        integrons_describe = integrons_describe[["ID_integron", "ID_replicon", "element", 
                                                 "pos_beg", "pos_end", "strand", "evalue",
                                                 "type_elt", "annotation", "model", 
                                                 "type", "default", "distance_2attC"]]
        integrons_describe['evalue'] = integrons_describe.evalue.astype(float)
        integrons_describe.index = range(len(integrons_describe))

        integrons_describe['evalue'] = integrons_describe['evalue'].map(lambda x: '%.3e' % x)
        integrons_describe.sort(["ID_integron","pos_beg", "evalue"], inplace=True)
        integrons_describe.to_csv(out_dir + outfile, sep="\t", index=0, fillna="NA")
        to_gbk(integrons_describe, SEQUENCE)
        SeqIO.write(SEQUENCE, out_dir + name + ".gbk", "genbank")


    else:
        out_f = open(out_dir + outfile, "w")
        out_f.write("# No Integron found\n")
        out_f.close()
