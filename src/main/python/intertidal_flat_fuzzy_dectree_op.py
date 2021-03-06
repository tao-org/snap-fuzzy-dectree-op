###################################################################################################
# This operator class implementation serves as a template for writing SNAP operators in Python.
# It is shown how thw source products and it's data is accessed, how the values
# of the parameters, specified in the accompanying generic_fuzzy_dectree_op-info.xml file, are retrieved and
# validated. Also how the resulting target product can be defined along with flags, masks, etc. is
# shown in this example. A guide about the development of a python operator can be found at
# http://senbox.atlassian.net/wiki/display/SNAP/How+to+write+a+processor+in+Python
# For further questions please consult the forum at http://forum.step.esa.int
###################################################################################################

import sys

for a in sys.path:
    print(a)

# import intertidal_flat_classif as fuzzy_classif
# import intertidal_flat_classif_opt as fuzzy_classif
import intertidal_flat_classif_fuz as fuzzy_classif

import numpy as np
import snappy

# If a Java type is needed which is not imported by snappy by default it can be retrieved manually.
# First import jpy
from snappy import jpy

# and then import the type
Float = jpy.get_type('java.lang.Float')
Color = jpy.get_type('java.awt.Color')

IndexCoding = jpy.get_type('org.esa.snap.core.datamodel.IndexCoding')
BandMathsType = jpy.get_type('org.esa.snap.core.datamodel.Mask$BandMathsType')
ColorPaletteDef = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef')
ColorPoint = jpy.get_type('org.esa.snap.core.datamodel.ColorPaletteDef$Point')
ImageInfo = jpy.get_type('org.esa.snap.core.datamodel.ImageInfo')

# _InputSpec = [
#     ("b1", float64[:]),      # sand-tr_abundance
#     ("b2", float64[:]),      # sand-wc_abundance
#     ("b3", float64[:]),      # schatten_abundance
#     ("b4", float64[:]),      # summary_error
#     ("b5", float64[:]),      # steigung_red_nIR
#     ("b6", float64[:]),      # steigung_nIR_SWIR1
#     ("b7", float64[:]),      # flh
#     ("b8", float64[:]),      # ndvi
#     ("b12", float64[:]),     # reflec_483
#     ("b13", float64[:]),     # reflec_561
#     ("b14", float64[:]),     # reflec_655
#     ("b15", float64[:]),     # reflec_865
#     ("b16", float64[:]),     # reflec_1609
#     ("b19", float64[:]),     # muschelindex
# ]

INPUT_NAMES = [
    ("b1", "sand-tr_abundance"),
    ("b2", "sand-wc_abundance"),
    ("b3", "schatten_abundance"),
    ("b4", "summary_error"),
    ("b5", "steigung_red_nIR"),
    ("b6", "steigung_nIR_SWIR1"),
    ("b7", "flh"),
    ("b8", "ndvi"),
    ("b12", "reflec_483"),
    ("b13", "reflec_561"),
    ("b14", "reflec_655"),
    ("b15", "reflec_865"),
    ("b16", "reflec_1609"),
    ("b19", "muschelindex")
]

# final class
INTERTIDAL_FLAT_CLASSIF_CLASS = np.array([
    11,  # nodata
    10,  # Wasser
    13,  # Schill
    8,  # Muschel
    7,  # dense2
    6,  # dense1
    9,  # Strand
    1,  # Sand
    2,  # Misch
    3,  # Misch2
    4,  # Schlick
    5,  # schlick_t
    12])  # Wasser2

# RGB code
INTERTIDAL_FLAT_CLASSIF_RGB = np.array([
    [0, 0, 0],  # nodata
    [0, 0, 255],  # Wasser
    [255, 113, 255],  # Schill
    [255, 0, 0],  # Muschel,
    [46, 139, 87],  # dense2
    [0, 255, 0],  # dense1
    [230, 230, 230],  # Strand
    [255, 255, 75],  # Sand
    [255, 215, 0],  # Misch
    [238, 154, 0],  # Misch2
    [125, 38, 205],  # Schlick
    [167, 80, 162],  # schlick_t
    [0, 60, 255]])  # Wasser2

OUTPUT_NAMES = [
    "nodata",
    "Wasser",
    "Schill",
    "Muschel",
    "dense2",
    "dense1",
    "Strand",
    "Sand",
    "Misch",
    "Misch2",
    "Schlick",
    "schlick_t",
    "Wasser2"
]


# _OutputSpec = [
#     ("nodata", float64[:]),
#     ("Wasser", float64[:]),
#     ("Schill", float64[:]),
#     ("Muschel", float64[:]),
#     ("dense2", float64[:]),
#     ("dense1", float64[:]),
#     ("Strand", float64[:]),
#     ("Sand", float64[:]),
#     ("Misch", float64[:]),
#     ("Misch2", float64[:]),
#     ("Schlick", float64[:]),
#     ("schlick_t", float64[:]),
#     ("Wasser2", float64[:]),
# ]


class IntertidalFlatFuzzyDectreeOp:
    def __init__(self):
        self.target_band = None

    def initialize(self, context):
        # Via the context object the source product which shall be processed can be retrieved
        source_product = context.getSourceProduct('source')
        print('initialize: source product location is', source_product.getFileLocation())

        width = source_product.getSceneRasterWidth()
        height = source_product.getSceneRasterHeight()

        self.source_bands = []
        for input_name, column_name in INPUT_NAMES:
            self.source_bands.append(source_product.getBand(column_name))

        # As it is always a good idea to separate responsibilities the algorithmic methods are put
        # into an other class

        # Create the target product
        target_product = snappy.Product('py_FuzzyDectree', 'py_FuzzyDectree', width, height)
        # ProductUtils provides several useful helper methods to build the target product.
        # In most cases it is sufficient to copy the information from the source to the target.
        # That's why mainly copy methods exist like copyBand(...), copyGeoCoding(...), copyMetadata(...)
        snappy.ProductUtils.copyGeoCoding(source_product, target_product)
        snappy.ProductUtils.copyMetadata(source_product, target_product)
        # For copying the time information no helper method exists yet, but will come in SNAP 5.0
        target_product.setStartTime(source_product.getStartTime())
        target_product.setEndTime(source_product.getEndTime())

        # Adding new bands to the target product is straight forward.
        self.target_bands = []
        for output_name in OUTPUT_NAMES:
            target_band = target_product.addBand(output_name, snappy.ProductData.TYPE_FLOAT32)
            self.target_bands.append(target_band)

        self.final_class_band = self.add_final_class_band(target_product)
        self.fuzzy_max_value_band = target_product.addBand('fuzzy_max_value', snappy.ProductData.TYPE_FLOAT32)
        # todo: flag band/mask ?!
        # flag_coding = self.create_flag_coding()
        # group = target_product.getFlagCodingGroup()
        # group.add(flag_coding)
        # self.final_class_band.setSampleCoding(flag_coding)
        # self.create_mask(target_product)

        # Provide the created target product to the framework so the computeTileStack method can be called
        # properly and the data can be written to disk.
        context.setTargetProduct(target_product)

    def computeTileStack(self, context, target_tiles, target_rectangle):
        # The operator is asked by the framework to provide the data for a rectangle when the data is needed.
        # The required source data for the computation can be retrieved by getSourceTile(...) via the context object.

        source_tiles = []
        for source_band in self.source_bands:
            source_tiles.append(context.getSourceTile(source_band, target_rectangle))

        # The actual data can be retrieved from the tiles by getSampleFloats(), getSamplesDouble() or getSamplesInt()
        # Values at specific pixel locations can be retrieved for example by first_tile.getSampleFloat(x, y)
        source_samples = []
        for source_tile in source_tiles:
            source_samples.append(source_tile.getSamplesFloat())

        source_data = []
        for source_sample in source_samples:
            source_data.append(np.array(source_sample, dtype=np.float64))
        source_data = np.asarray(source_data)

        classif_input = fuzzy_classif.Input(source_data[0].size)
        classif_input.b1 = source_data[0]
        classif_input.b2 = source_data[1]
        classif_input.b3 = source_data[2]
        classif_input.b4 = source_data[3]
        classif_input.b5 = source_data[4]
        classif_input.b6 = source_data[5]
        classif_input.b7 = source_data[6]
        classif_input.b8 = source_data[7]
        classif_input.b12 = source_data[8]
        classif_input.b13 = source_data[9]
        classif_input.b14 = source_data[10]
        classif_input.b15 = source_data[11]
        classif_input.b16 = source_data[12]
        classif_input.b19 = source_data[13]
        classif_input.bsum = source_data[8] + source_data[9] + source_data[10]  # b12 + b13 + b14

        classif_output = fuzzy_classif.Output(classif_input.b1.size)

        target_samples = [classif_output.nodata, classif_output.Wasser, classif_output.Schill, classif_output.Muschel,
                          classif_output.dense2, classif_output.dense1, classif_output.Strand, classif_output.Sand,
                          classif_output.Misch, classif_output.Misch2, classif_output.Schlick, classif_output.schlick_t,
                          classif_output.Wasser2]

        # Doing the actual computation
        fuzzy_classif.apply_rules(classif_input, classif_output)

        # The target tile which shall be filled with data are provided as parameter to this method
        for i in range(0, len(self.target_bands)):
            target_tiles.get(self.target_bands[i]).setSamples(target_samples[i])

        # find pixel-wise maximum of classif_output to determine final class
        target_samples_np = np.array(target_samples)
        max_indices = np.argmax(target_samples_np, axis=0)
        final_class_data = INTERTIDAL_FLAT_CLASSIF_CLASS[max_indices]
        target_tiles.get(self.final_class_band).setSamples(final_class_data)

        fuzzy_max_values = np.amax(target_samples_np, axis=0)
        target_tiles.get(self.fuzzy_max_value_band).setSamples(fuzzy_max_values)

    def dispose(self, context):
        pass

    def _get_band(self, product, name):
        # Retrieve the band from the product
        # Some times data is not stored in a band but in a tie-point grid or a mask or a vector data.
        # To get access to this information other methods are exposed by the product class. Like
        # getTiePointGridGroup().get('name'), getVectorDataGroup().get('name') or getMaskGroup().get('name')
        # For bands and tie-point grids a short cut exists. Simply use getBand('name') or getTiePointGrid('name')
        band = product.getBandGroup().get(name)
        if not band:
            raise RuntimeError('Product does not contain a band named', name)
        return band

    def create_flag_coding(self):

        # todo: discuss (not yet needed)
        fuzzyDecFlagCoding = snappy.FlagCoding('fuzzy_dec_flags')
        fuzzyDecFlagCoding.addFlag("Muschel", 1, "Muschel")
        fuzzyDecFlagCoding.addFlag("Schill", 2, "Schill")
        fuzzyDecFlagCoding.addFlag("Sand", 4, "Sand")
        fuzzyDecFlagCoding.addFlag("Schlick", 8, "Schlick")
        fuzzyDecFlagCoding.addFlag("Misch", 16, "Misch")
        fuzzyDecFlagCoding.addFlag("schlick_t", 32, "schlick_t")
        fuzzyDecFlagCoding.addFlag("Strand", 64, "Strand")
        fuzzyDecFlagCoding.addFlag("nodata", 128, "nodata")
        fuzzyDecFlagCoding.addFlag("Wasser2", 256, "Wasser2")
        fuzzyDecFlagCoding.addFlag("Wasser", 512, "Wasser")
        fuzzyDecFlagCoding.addFlag("dense2", 1024, "dense2")
        fuzzyDecFlagCoding.addFlag("dense1", 2048, "dense1")
        fuzzyDecFlagCoding.addFlag("Misch2", 4096, "Misch2")

        return fuzzyDecFlagCoding

    def create_mask(self, product):

        # todo: discuss (not yet needed)
        index = 0
        w = product.getSceneRasterWidth()
        h = product.getSceneRasterHeight()

        mask = snappy.Mask.BandMathsType.create("MUSCHEL", "MUSCHEL", w, h, "Muschel", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("SCHILL", "SCHILL", w, h, "Schill", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("SAND", "SAND", w, h, "Sand", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("SCHLICK", "SCHLICK", w, h, "Schlick", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("MISCH", "MISCH", w, h, "Misch", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("SCHLICK_T", "SCHLICK_T", w, h, "schlick_t", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("STRAND", "STRAND", w, h, "Strand", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("NODATA", "NODATA", w, h, "nodata", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("WASSER2", "WASSER2", w, h, "Wasser2", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("WASSER", "WASSER", w, h, "Wasser", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("DENSE2", "DENSE2", w, h, "dense2", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("DENSE", "DENSE", w, h, "dense", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)
        index += 1
        mask = snappy.Mask.BandMathsType.create("MISCH2", "MISCH2", w, h, "Misch2", Color(255, 0, 0), 0.5)
        product.getMaskGroup().add(index, mask)

    def add_final_class_band(self, target_product):
        final_class_band = target_product.addBand('final_class', snappy.ProductData.TYPE_INT8)

        index_coding = IndexCoding('final_class')

        points = []
        for i in range(0, len(INTERTIDAL_FLAT_CLASSIF_CLASS)):
            value = np.asscalar(INTERTIDAL_FLAT_CLASSIF_CLASS[i])
            r = np.asscalar(INTERTIDAL_FLAT_CLASSIF_RGB[i][0])
            g = np.asscalar(INTERTIDAL_FLAT_CLASSIF_RGB[i][1])
            b = np.asscalar(INTERTIDAL_FLAT_CLASSIF_RGB[i][2])
            col = Color(r, g, b)
            descr = OUTPUT_NAMES[i]
            point = ColorPoint(value, col, descr)
            points.append(point)
            index_coding.addIndex(descr, value, descr)

        cpd = ColorPaletteDef(points)
        ii = ImageInfo(cpd)
        final_class_band.setImageInfo(ii)

        target_product.getIndexCodingGroup().add(index_coding)
        final_class_band.setSampleCoding(index_coding)

        return final_class_band
