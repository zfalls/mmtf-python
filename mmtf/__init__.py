import gzip
import time
try:
    import urllib2
    from StringIO import StringIO
except:
    import urllib.request as urllib2
    from io import BytesIO as StringIO

import msgpack
from mmtf.codecs import decode_array,encode_array
from mmtf import decoder_utils
COORD_DIVIDER = 1000.0
OCC_B_FACTOR_DIVIDER = 100.0
MAX_SHORT = 32767
MIN_SHORT = -32768
NULL_BYTE = '\x00'
CHAIN_LEN = 4
NUM_DICT = {1:'b',2:'>h',4:'>i'}
BASE_URL = "http://mmtf.rcsb.org/v0.2/full/"

class MMTFDecoder():
    """Class to decode raw mmtf data into a parsed data model that can be fed into
    other data model"""
    model_counter = 0
    chain_counter = 0
    group_counter = 0
    atom_counter = 0
    def decode_data(self, input_data):
        self.group_list = decode_array(input_data[b"groupTypeList"])
        # Decode the coordinate  and B-factor arrays.
        self.cartnX = decode_array(input_data[b"xCoordList"])
        self.cartnY = decode_array(input_data[b"yCoordList"])
        self.cartnZ = decode_array(input_data[b"zCoordList"])
        # Run length decode the occupancy array
        if b"bFactorList" in input_data:
            self.b_factor = decode_array(input_data[b"bFactorList"])
        else:
            self.b_factor = []
        if b"occupancyList" in input_data:
            self.occupancy = decode_array(input_data[b"occupancyList"])
        else:
            self.occupancy = []
        # Run length and delta
        if b"atomIdList" in input_data:
            self.atom_id = decode_array(input_data[b"atomIdList"])
        else:
            self.atom_id = []
        # Run length encoded
        if "altLocList" in input_data:
            self.alt_id = decode_array(input_data[b"altLocList"])
        else:
            self.alt_id = []
        if "insCodeList" in input_data:
            self.insertion_code_list = decode_array(input_data[b"insCodeList"])
        else:
            self.insertion_code_list = []
        # Get the group_number
        self.group_num = decode_array(input_data[b"groupIdList"])
        # Get the group map (all the unique groups in the structure).
        self.group_map = input_data[b"groupList"]
        # Get the seq_res groups
        if "sequenceIndexList" in input_data:
            self.seq_res_group_list = decode_array(input_data[b"sequenceIndexList"])
        else:
            self.seq_res_group_list = []
        # Get the number of chains per model
        self.chains_per_model = input_data[b"chainsPerModel"]
        self.groups_per_chain = input_data[b"groupsPerChain"]
        # Get the internal and public facing chain ids
        if b"chainNameList" in input_data:
            self.public_chain_ids = decode_array(input_data[b"chainNameList"])
        else:
            self.public_chain_ids = []
        self.chain_list = decode_array(input_data[b"chainIdList"])
        self.space_group = input_data[b"spaceGroup"]
        self.inter_group_bond_indices = decode_array(input_data[b"bondAtomList"])
        self.inter_group_bond_orders = decode_array(input_data[b"bondOrderList"])
        self.mmtf_version = input_data[b"mmtfVersion"]
        self.mmtf_producer = input_data[b"mmtfProducer"]
        self.structure_id = input_data[b"structureId"]
        # Now get the header data
        # Optional fields
        if b"entityList" in input_data:
            self.entity_list = input_data[b"entityList"]
        else:
            self.entity_list = []
        if b"bioAssemblyList" in input_data:
            self.bio_assembly = input_data[b"bioAssemblyList"]
        else:
            self.bio_assembly = []
        if b"rFree" in input_data:
            self.r_free = input_data[b"rFree"]
        else:
            self.r_free = None
        if b"rWork" in input_data:
            self.r_work = input_data[b"rWork"]
        else:
            self.r_work = None
        if b"resolution" in input_data:
            self.resolution = input_data[b"resolution"]
        if b"title" in input_data:
            self.title = input_data[b"title"]
        if b"experimentalMethods" in input_data:
            self.experimental_methods = input_data[b"experimentalMethods"]
        else:
            self.experimental_methods = None
        # Now get the relase information
        if b"depositionData" in input_data:
            self.deposition_date = input_data[b"depositionDate"]
        else:
            self.deposition_date = None
        if b"releaseDate" in input_data:
            self.release_date = input_data[b"releaseDate"]
        else:
            self.release_date = None
        if b"unitCell" in input_data:
            self.unit_cell = input_data[b"unitCell"]
        else:
            self.unit_cell = None

        self.sec_struct_info = decode_array(input_data[b"secStructList"])
        self.num_bonds = input_data[b"numBonds"]
        self.num_chains = input_data[b"numChains"]
        self.num_models = input_data[b"numModels"]
        self.num_atoms = input_data[b"numAtoms"]
        self.num_groups = input_data[b"numGroups"]
    #
    # {10: DeltaRecursiveFloat,
    #  9: RunLengthFloat,
    #  8: RunLengthDeltaInt,
    #  6: RunLengthChar,
    #  5: EncodeString,
    #  4: ByteToInt,
    #  2: FourByteToInt}
    def encode_data(self):
        output_data = {}
        output_data[b"groupTypeList"] = encode_array(self.group_list,2,0)
        # Decode the coordinate  and B-factor arrays.
        output_data[b"xCoordList"] = encode_array(self.cartnX,10,1000)
        output_data[b"yCoordList"] = encode_array(self.cartnY, 10, 1000)
        output_data[b"zCoordList"] = encode_array(self.cartnZ, 10, 1000)
        # Run length decode the occupancy array
        output_data[b"bFactorList"] = encode_array(self.b_factor, 10, 100)
        # Run length float
        output_data[b"occupancyList"] = encode_array(self.occupancy,9,100)
        # Run length delta
        output_data[b"atomIdList"] = encode_array(self.atom_id,8,0)
        # Run length encoded
        output_data[b"altLocList"] = encode_array(self.alt_id,6,0)
        output_data[b"insCodeList"] = encode_array(self.insertion_code_list,6,0)
        # Get the group_number
        output_data[b"groupIdList"] = encode_array(self.group_num,4,0)
        # Get the group map (all the unique groups in the structure).
        output_data[b"groupList"] = self.group_map
        # Get the seq_res groups
        output_data[b"sequenceIndexList"] = encode_array(self.seq_res_group_list,8,0)
        # Get the internal and public facing chain ids
        output_data[b"chainNameList"] = encode_array(self.public_chain_ids,5,0)
        output_data[b"chainIdList"] = encode_array(self.chain_list,5,0)
        output_data[b"bondAtomList"] = encode_array(self.inter_group_bond_indices,4,0)
        output_data[b"bondOrderList"] =  encode_array(self.inter_group_bond_orders,2,0)
        output_data[b"secStructList"] = encode_array(self.sec_struct_info,2,0)
        # Get the number of chains per model
        output_data[b"chainsPerModel"] = self.chains_per_model
        output_data[b"groupsPerChain"] = self.groups_per_chain
        output_data[b"spaceGroup"] = self.space_group
        output_data[b"mmtfVersion"] = self.mmtf_version
        output_data[b"mmtfProducer"] = self.mmtf_producer
        output_data[b"structureId"] = self.structure_id
        # Now get the header data
        # Optional fields
        output_data[b"entityList"] = self.entity_list
        output_data[b"bioAssemblyList"] = self.bio_assembly
        output_data[b"rFree"] = self.r_free
        output_data[b"rWork"] = self.r_work
        output_data[b"resolution"] = self.resolution
        output_data[b"title"] = self.title
        output_data[b"experimentalMethods"] = self.experimental_methods
        # Now get the relase information
        output_data[b"depositionDate"] = self.deposition_date
        output_data[b"releaseDate"] = self.release_date
        output_data[b"unitCell"] = self.unit_cell
        output_data[b"numBonds"] = self.num_bonds
        output_data[b"numChains"] = self.num_chains
        output_data[b"numModels"] = self.num_models
        output_data[b"numAtoms"] = self.num_atoms
        output_data[b"numGroups"]= self.num_groups
        return output_data


    def pass_data_on(self, data_setters):
        """Write the data from the getters to the setters
        :type data_setters: DataTransferInterface
        """
        data_setters.init_structure(self.num_bonds, len(self.cartnX), len(self.group_list),
                                   len(self.chain_list), len(self.chains_per_model), self.structure_id)
        # Set the entity information
        decoder_utils.add_entity_info(self, data_setters)
        # First add the atomic data
        decoder_utils.add_atomic_information(self, data_setters)
        # Set the header info
        decoder_utils.add_header_info(self, data_setters)
        # Set the xtalographic info
        decoder_utils.add_xtalographic_info(self, data_setters)
        # Set the bioassembly info
        decoder_utils.generate_bio_assembly(self, data_setters)
        # Set the intergroup bonds
        decoder_utils.add_inter_group_bonds(self, data_setters)
        # Finally call the finalize function
        data_setters.finalize_structure()


    def get_msgpack(self):
        """Get the msgpack of the encoded data"""
        return msgpack.packb(self.encode_data())



def get_raw_data_from_url(pdb_id):
    """" Get the msgpack unpacked data given a PDB id.
    :param the input PDB id
    :return the unpacked data (a dict) """
    url = BASE_URL + pdb_id
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)
    if response.info().get('Content-Encoding') == 'gzip':
        data = ungzip_data(response.read())
    out_data = msgpack.unpackb(data)
    return out_data


def fetch(pdb_id):
    """Return a decoded API to the data from a PDB id
    :param the input PDB id
    :return an API to decoded data """
    decoder = MMTFDecoder()
    decoder.decode_data(get_raw_data_from_url(pdb_id))
    return decoder


def ungzip_data(input_data):
    """Retrun a string of data after gzip decoding
    :param the input GZIPed data
    :return  the GZIP decoded data"""
    buf = StringIO(input_data)
    f = gzip.GzipFile(fileobj=buf)
    data = f.read()
    return data