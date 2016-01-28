from collections import Counter
import math

PERIODIC_TABLE = {
 "H": 1.0079, "HE": 4.0026, "LI": 6.941, "BE": 9.0122, "B": 10.811, "C": 12.0107,
  "N": 14.0067, "O": 15.9994, "F": 18.9984, "NE": 20.1797, "NA": 22.9897, "MG": 24.305,
   "AL": 26.9815, "SI": 28.0855, "P": 30.9738, "S": 32.065, "CL": 35.453, "K": 39.0983,
    "AR": 39.948, "CA": 40.078, "SC": 44.9559, "TI": 47.867, "V": 50.9415, "CR": 51.9961,
     "MN": 54.938, "FE": 55.845, "NI": 58.6934, "CO": 58.9332, "CU": 63.546, "ZN": 65.39,
      "GA": 69.723, "GE": 72.64, "AS": 74.9216, "SE": 78.96, "BR": 79.904, "KR": 83.8,
       "RB": 85.4678, "SR": 87.62, "Y": 88.9059, "ZR": 91.224, "NB": 92.9064, "MO": 95.94,
        "TC": 98, "RU": 101.07, "RH": 102.9055, "PD": 106.42, "AG": 107.8682, "CD": 112.411,
         "IN": 114.818, "SN": 118.71, "SB": 121.76, "I": 126.9045, "TE": 127.6,
          "XE": 131.293, "CS": 132.9055, "BA": 137.327, "LA": 138.9055, "CE": 140.116,
           "PR": 140.9077, "ND": 144.24, "PM": 145, "SM": 150.36, "EU": 151.964,
            "GD": 157.25, "TB": 158.9253, "DY": 162.5, "HO": 164.9303, "ER": 167.259,
             "TM": 168.9342, "YB": 173.04, "LU": 174.967, "HF": 178.49, "TA": 180.9479,
              "W": 183.84, "RE": 186.207, "OS": 190.23, "IR": 192.217, "PT": 195.078,
               "AU": 196.9665, "HG": 200.59, "TL": 204.3833, "PB": 207.2, "BI": 208.9804,
                "PO": 209, "AT": 210, "RN": 222, "FR": 223, "RA": 226, "AC": 227,
                 "PA": 231.0359, "TH": 232.0381, "NP": 237, "U": 238.0289, "AM": 243,
                  "PU": 244, "CM": 247, "BK": 247, "CF": 251, "ES": 252, "FM": 257,
                   "MD": 258, "NO": 259, "RF": 261, "LR": 262, "DB": 262, "BH": 264,
                    "SG": 266, "MT": 268, "RG": 272, "HS": 277, "X": 0, "D": 0}

class PdbStructure:
    """A representation of the contents of a PDB file."""

    def __init__(self, pdb_data):
        self.data = pdb_data

        self.models = [Model(d, self.data.miscellaneous.sites,
         self.data.secondary_structure, self.data.connectivity)
          for d in self.data.coordinates.models]
        self.model = self.models[0]



class AtomicStructure:
    """Some structure that contains atoms."""

    def __init__(self, atoms):
        self.atoms = atoms
        self.mass = sum([a.mass for a in self.atoms])


    def __repr__(self):
        return ", ".join([str(a) for a in self.atoms])


    def get_atom_by_number(self, number):
        for atom in self.atoms:
            if atom.number == number:
                return atom


    def get_atoms_by_name(self, name):
        return [a for a in self.atoms if a.name == name]


    def get_atoms_by_element(self, element):
        return [a for a in self.atoms if a.element == element]


    def get_atom_counts(self):
        atoms = [atom.element.upper() for atom in self.atoms if atom.element.upper() != "H"]
        return Counter(atoms)



class ResiduicStructure(AtomicStructure):
    """Some structure that contains residues."""

    def __init__(self, residues):
        self.residues = residues
        atoms = []
        for residue in self.residues:
            atoms += residue.atoms
        AtomicStructure.__init__(self, atoms)


    def __repr__(self):
        return ", ".join([str(r) for r in self.residues])


    def __len__(self):
        return len(self.residues)


    def get_residues_by_chain(self, chain_id):
        return [r for r in self.residues if r.chain.name == chain_id]


    def get_residues_by_name(self, name):
        return [r for r in self.residues if r.name == name]


    def get_residue_by_number(self, number):
        """Returns the first residue with a matching number."""
        for residue in self.residues:
            if residue.number == number:
                return residue


    def get_residues_by_number(self, number):
        """Returns all residues with matching number."""
        return [r for r in self.residues if r.number == number]


    def get_continuous_sequence(self):
        """If all the residues are on the same chain, return an unbroken
        string of residues that contains all residues in this orginal structure."""

        if len(self.residues) > 1:
            if all([r.chain is self.residues[0].chain for r in self.residues[1:]]):
                #All residues are on the same chain
                return ResiduicStructure(
                 [r for r in self.residues[0].chain.residues if
                  r.number >= min([res.number for res in self.residues]) and
                   r.number <= max([res.number for res in self.residues])]
                )
        else:
            return self



class Model(AtomicStructure):
    """A PDB model."""

    def __init__(self, model_dict, site_dicts, secondary_section, connect_section):
        #Get chains
        chain_ids = sorted(list(set([a["chain_id"] for a in model_dict["atoms"] if not a["het"]])))
        self.chains = [Chain(
         [a for a in model_dict["atoms"] if a["chain_id"] == chain_id and not a["het"]],
         [t for t in model_dict["ters"] if t["chain_id"] == chain_id],
         [h for h in secondary_section.helices if h["start_residue_chain"] == chain_id]
        ) for chain_id in chain_ids]
        atoms = []
        for chain in self.chains:
            atoms += chain.atoms

        #Get hets
        het_numbers = sorted(list(set([a["res_seq"] for a in model_dict["atoms"] if a["het"]])))
        self.hets = [Het(
         [a for a in model_dict["atoms"] if a["res_seq"] == het_number]
        ) for het_number in het_numbers]
        for het in self.hets:
            atoms += het.atoms
        AtomicStructure.__init__(self, atoms)
        for atom in self.atoms:
            atom.model = self

        #Get sites
        self.pdb_sites = [PdbSite(s, self) for s in site_dicts]

        #Get helices
        self.helices = []
        for chain in self.chains:
            self.helices += chain.helices

        #Get sheets
        self.sheets = [Sheet(s, self) for s in secondary_section.sheets]

        #Connect atoms together (from CONECT records)
        for atom_dict in connect_section.atoms:
            atom_obj = self.get_atom_by_number(atom_dict["atom_id"])
            for bonded_atom_id in atom_dict["bonded_atoms"]:
                bonded_atom_obj = self.get_atom_by_number(bonded_atom_id)
                if bonded_atom_obj not in atom_obj.bonded_atoms:
                    atom_obj.bonded_atoms.append(bonded_atom_obj)

        #Connect atoms together (standard residues)
        from .residues import residues
        for chain in self.chains:
            for residue in chain.residues:
                if residue.name in residues.keys():
                    residue_dict = residues[residue.name]
                    for atom_name in residue_dict.keys():
                        matching_atoms = residue.get_atoms_by_name(atom_name)
                        if len(matching_atoms) == 1:
                            atom = matching_atoms[0]
                            for bonded_atom_name in residue_dict[atom_name]:
                                matching_atoms = residue.get_atoms_by_name(bonded_atom_name)
                                if len(matching_atoms) == 1 and matching_atoms[0] not in atom.bonded_atoms:
                                    atom.bonded_atoms.append(matching_atoms[0])





    def __repr__(self):
        return "<Model (%i atoms)>" % len(self.atoms)


    def get_chain_by_name(self, name):
        for chain in self.chains:
            if chain.name == name:
                return chain


    def get_het_by_number(self, number):
        for het in self.hets:
            if het.number == number:
                return het


class Chain(ResiduicStructure):
    "A chain of residues."

    def __init__(self, atoms, termini, helix_dicts):
        self.name = atoms[0]["chain_id"]

        #Get residues
        residue_numbers = sorted(list(set([a["res_seq"] for a in atoms])))
        residues = [Residue(
         [a for a in atoms if a["res_seq"] == residue_number]
        ) for residue_number in residue_numbers]
        ResiduicStructure.__init__(self, residues)
        for residue in self.residues:
            residue.chain = self

        #Specify terminating residue
        if len(termini) == 1:
            matching_residue = [r for r in self.residues if r.number == termini[0]["res_seq"]]
            if matching_residue:
                matching_residue[0].terminus = True

        #Get helices
        self.helices = [Helix(h, self) for h in helix_dicts]

        self.strands = [] #Gets filled in later



    def __repr__(self):
        return "<Chain %s (%i residues)>" % (self.name, len(self.residues))



class Residue(AtomicStructure):
    "An amino acid residue."

    RESIDUE_NAMES = {
     "phenylalanine": ("PHE", "F"), "PHE": ("phenylalanine", "F"), "F": ("phenylalanine", "PHE"),
      "tryptophan": ("TRP", "W"), "TRP": ("tryptophan", "W"), "W": ("tryptophan", "TRP"),
       "methionine": ("MET", "M"), "MET": ("methionine", "M"), "M": ("methionine", "MET"),
        "isoleucine": ("ILE", "I"), "ILE": ("isoleucine", "I"), "I": ("isoleucine", "ILE"),
         "asparagine": ("ASN", "N"), "ASN": ("asparagine", "N"), "N": ("asparagine", "ASN"),
          "threonine": ("THR", "T"), "THR": ("threonine", "T"), "T": ("threonine", "THR"),
           "histidine": ("HIS", "H"), "HIS": ("histidine", "H"), "H": ("histidine", "HIS"),
            "glutamine": ("GLN", "Q"), "GLN": ("glutamine", "Q"), "Q": ("glutamine", "GLN"),
             "glutamate": ("GLU", "E"), "GLU": ("glutamate", "E"), "E": ("glutamate", "GLU"),
              "aspartate": ("ASP", "D"), "ASP": ("aspartate", "D"), "D": ("aspartate", "ASP"),
               "tyrosine": ("TYR", "Y"), "TYR": ("tyrosine", "Y"), "Y": ("tyrosine", "TYR"),
                "cysteine": ("CYS", "C"), "CYS": ("cysteine", "C"), "C": ("cysteine", "CYS"),
                 "arginine": ("ARG", "R"), "ARG": ("arginine", "R"), "R": ("arginine", "ARG"),
                  "proline": ("PRO", "P"), "PRO": ("proline", "P"), "P": ("proline", "PRO"),
                   "leucine": ("LEU", "L"), "LEU": ("leucine", "L"), "L": ("leucine", "LEU"),
                    "glycine": ("GLY", "G"), "GLY": ("glycine", "G"), "G": ("glycine", "GLY"),
                     "alanine": ("ALA", "A"), "ALA": ("alanine", "A"), "A": ("alanine", "ALA"),
                      "valine": ("VAL", "V"), "VAL": ("valine", "V"), "V": ("valine", "VAL"),
                       "serine": ("SER", "S"), "SER": ("serine", "S"), "S": ("serine", "SER"),
                        "lysine": ("LYS", "K"), "LYS": ("lysine", "K"), "K": ("lysine", "LYS")
    }

    def __init__(self, atoms):
        self.number = atoms[0]["res_seq"]
        self.name = atoms[0]["res_name"]
        self.terminus = False

        #Get atoms
        AtomicStructure.__init__(self, [Atom(a) for a in atoms])
        for atom in self.atoms:
            atom.molecule = self


    def __repr__(self):
        return "<%s (%s%i)>" % (self.name, self.chain.name, self.number)



class Atom:
    """An atom."""

    def __init__(self, atom_dict):
        self.number = atom_dict["serial"]
        self.name = atom_dict["name"]
        self.insert_code = atom_dict["i_code"]
        self.x = atom_dict["x"]
        self.y = atom_dict["y"]
        self.z = atom_dict["z"]
        self.occupancy = atom_dict["occupancy"]
        self.temp_factor = atom_dict["temp_factor"]
        self.element = atom_dict["element"]
        self.charge = atom_dict["charge"]
        self.u11 = atom_dict.get("u11", None)
        self.u22 = atom_dict.get("u22", None)
        self.u33 = atom_dict.get("u33", None)
        self.u12 = atom_dict.get("u12", None)
        self.u13 = atom_dict.get("u13", None)
        self.u23 = atom_dict.get("u23", None)

        self.mass = PERIODIC_TABLE[self.element.upper()]
        self.bonded_atoms = []


    def __repr__(self):
        return "<%s>" % self.name


    def distance_to(self, other_atom):
        x_sum = math.pow((other_atom.x - self.x), 2)
        y_sum = math.pow((other_atom.y - self.y), 2)
        z_sum = math.pow((other_atom.z - self.z), 2)
        distance = math.sqrt(x_sum + y_sum + z_sum)
        return distance


    def nearby_atoms(self, cutoff, include_covalent=True):
        atoms = []
        for atom in self.model.atoms:
            if (include_covalent or atom not in self.bonded_atoms) and atom is not self and atom.distance_to(self) <= cutoff:
                atoms.append(atom)
        return atoms



class Het(AtomicStructure):
    """A ligand or other non-polymeric molecule (including solvents)."""

    def __init__(self, atoms):
        self.number = atoms[0]["res_seq"]
        self.name = atoms[0]["res_name"]

        #Get atoms
        AtomicStructure.__init__(self, [Atom(a) for a in atoms])
        for atom in self.atoms:
            atom.molecule = self


    def __repr__(self):
        return "<%s (%i atom%s)>" % (self.name, len(self.atoms), "" if len(self.atoms) == 1 else "s")




class PdbSite(ResiduicStructure):
    """A site named in the PDB file."""

    def __init__(self, site_dict, model):
        self.name = site_dict["name"]

        residues = []
        self.hets = []
        for residue_dict in site_dict["residues"]:
            chain = model.get_chain_by_name(residue_dict["chain"])
            if chain:
                residue = chain.get_residue_by_number(residue_dict["residue_number"])
                if residue:
                    residues.append(residue)
            het = model.get_het_by_number(residue_dict["residue_number"])
            if het:
                self.hets.append(het)
        ResiduicStructure.__init__(self, residues)


    def __repr__(self):
        return "<%s: %s>" % (self.name, ", ".join([str(r) for r in self.residues + self.hets]))


class Helix(ResiduicStructure):
    """An alpha helix."""

    CLASSES = {1: "Right-handed alpha", 2: "Right-handed omega", 3: "Right-handed pi",
     4: "Right-handed gamma", 5: "Right-handed 3 - 10", 6: "Left-handed alpha", 7: "Left-handed omega",
      8: "Left-handed gamma", 9: "2 - 7 ribbon/helix", 10: "Polyproline"}

    def __init__(self, helix_dict, chain):
        self.number = helix_dict["serial"]
        self.name = helix_dict["helix_id"]
        self.chain = chain
        residues = [chain.get_residue_by_number(i) for i in
         range(helix_dict["start_residue_number"], helix_dict["end_residue_number"] + 1)]
        residues = [r for r in residues if r] #Important if file lists residue that doesn't exist
        ResiduicStructure.__init__(self, residues)
        self.helix_class = self.CLASSES[helix_dict["helix_class"] if helix_dict["helix_class"] else 1]
        self.comment = helix_dict["comment"]



class Sheet(ResiduicStructure):
    """A beta sheet."""

    def __init__(self, sheet_dict, model):
        self.name = sheet_dict["sheet_id"]
        self.strands = [Strand(sheet_dict["strands"][0], model)]
        for strand_dict in sheet_dict["strands"][1:]:
            self.strands.append(Strand(strand_dict, model, self.strands[-1]))
        residues = []
        for strand in self.strands:
            residues += strand.residues
        ResiduicStructure.__init__(self, residues)


    def __repr__(self):
        return "<Beta sheet %s (%i strands)>" % (self.name, len(self.strands))



class Strand(ResiduicStructure):
    """A beta strand."""

    def __init__(self, strand_dict, model, previous_strand=None):
        self.number = strand_dict["strand_id"]
        self.name = self.number
        self.chain = model.get_chain_by_name(strand_dict["start_residue_chain"])
        self.chain.strands.append(self)
        residues = [self.chain.get_residue_by_number(i) for i in
         range(strand_dict["start_residue_number"], strand_dict["end_residue_number"] + 1)]
        residues = [r for r in residues if r] #Important if file lists residue that doesn't exist
        ResiduicStructure.__init__(self, residues)
        self.sense = strand_dict["sense"]

        if previous_strand:
            self.previous_strand = previous_strand
            self.registration = (
             self.get_atoms_by_name(strand_dict["reg_cur_atom"])[0]
              if self.get_atoms_by_name(strand_dict["reg_cur_atom"]) else None,
             self.get_atoms_by_name(strand_dict["reg_prev_atom"])[0]
              if self.get_atoms_by_name(strand_dict["reg_prev_atom"]) else None
            )
        else:
            self.previous_strand, self.registration = None, None
