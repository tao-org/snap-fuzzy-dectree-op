###################################################################################################
# This operator class implementation serves as a template for writing SNAP operators in Python.
# It is shown how thw source products and it's data is accessed, how the values
# of the parameters, specified in the accompanying fuzzy_dectree_op-info.xml file, are retrieved and
# validated. Also how the resulting target product can be defined along with flags, masks, etc. is
# shown in this example. A guide about the development of a python operator can be found at
# http://senbox.atlassian.net/wiki/display/SNAP/How+to+write+a+processor+in+Python
# For further questions please consult the forum at http://forum.step.esa.int
###################################################################################################

import fuzzy_dectree_algo
import intertidal_flat_classif

import numpy
import snappy

# If a Java type is needed which is not imported by snappy by default it can be retrieved manually.
# First import jpy
from snappy import jpy

# and then import the type
Float = jpy.get_type('java.lang.Float')
Color = jpy.get_type('java.awt.Color')


class FuzzyDectreeOp:
    def __init__(self):
        self.target_band = None

    def initialize(self, context):
        # Via the context object the source product which shall be processed can be retrieved
        source_product = context.getSourceProduct('source')
        print('initialize: source product location is', source_product.getFileLocation())

        width = source_product.getSceneRasterWidth()
        height = source_product.getSceneRasterHeight()

        # _InputSpec = [
        #     ("b16", float64[:]),     # reflec_1609
        #     ("b2", float64[:]),      # sand-wc_abundance
        #     ("bsum", float64[:]),    # b12 + b13 + b14
        #     ("b19", float64[:]),     # muschelindex
        #     ("b3", float64[:]),      # schatten_abundance
        #     ("b13", float64[:]),     # reflec_561
        #     ("b7", float64[:]),      # flh
        #     ("b15", float64[:]),     # reflec_865
        #     ("b4", float64[:]),      # summary_error
        #     ("b14", float64[:]),     # reflec_655
        #     ("b5", float64[:]),      # steigung_red_nIR
        #     ("b8", float64[:]),      # ndvi
        #     ("b100", float64[:]),    # summary_error
        #     ("b6", float64[:]),      # steigung_nIR_SWIR1
        #     ("b1", float64[:]),      # sand-tr_abundance
        #     ("b12", float64[:]),     # reflec_483
        # ]

        self.band_b16 = source_product.getBand("reflec_1609")
        self.band_b2 = source_product.getBand("wc_abundance")
        self.band_b19 = source_product.getBand("muschelindex")
        self.band_b3 = source_product.getBand("schatten_abundance")
        self.band_b13 = source_product.getBand("reflec_561")
        self.band_b7 = source_product.getBand("flh")
        self.band_b15 = source_product.getBand("reflec_865")
        self.band_b4 = source_product.getBand("summary_error")
        self.band_b14 = source_product.getBand("reflec_655")
        self.band_b5 = source_product.getBand("steigung_red_nIR")
        self.band_b8 = source_product.getBand("ndvi")
        self.band_b6 = source_product.getBand("steigung_nIR_SWIR1")
        self.band_b1 = source_product.getBand("sand")
        self.band_b12 = source_product.getBand("reflec_483")

        # As it is always a good idea to separate responsibilities the algorithmic methods are put
        # into an other class
        self.algo = fuzzy_dectree_algo.FuzzyDectreeAlgo()

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

        # _OutputSpec = [
        #     ("Muschel", float64[:]),
        #     ("Schill", float64[:]),
        #     ("Sand", float64[:]),
        #     ("Schlick", float64[:]),
        #     ("Misch", float64[:]),
        #     ("schlick_t", float64[:]),
        #     ("Strand", float64[:]),
        #     ("nodata", float64[:]),
        #     ("Wasser2", float64[:]),
        #     ("Wasser", float64[:]),
        #     ("dense2", float64[:]),
        #     ("dense1", float64[:]),
        #     ("Misch2", float64[:]),
        # ]

        # todo : what do we want to have in the target product? All output?
        self.muschel_band = target_product.addBand('Muschel', snappy.ProductData.TYPE_FLOAT32)
        self.schill_band = target_product.addBand('Schill', snappy.ProductData.TYPE_FLOAT32)
        self.sand_band = target_product.addBand('Sand', snappy.ProductData.TYPE_FLOAT32)
        self.schlick_band = target_product.addBand('Schlick', snappy.ProductData.TYPE_FLOAT32)
        self.misch_band = target_product.addBand('Misch', snappy.ProductData.TYPE_FLOAT32)
        self.schlick_t_band = target_product.addBand('Schlick_t', snappy.ProductData.TYPE_FLOAT32)
        self.strand_band = target_product.addBand('Strand', snappy.ProductData.TYPE_FLOAT32)
        self.nodata_band = target_product.addBand('Wasser2', snappy.ProductData.TYPE_FLOAT32)
        self.wasser2_band = target_product.addBand('Wasser', snappy.ProductData.TYPE_FLOAT32)
        self.wasser_band = target_product.addBand('Muschel', snappy.ProductData.TYPE_FLOAT32)
        self.dense2_band = target_product.addBand('Dense2', snappy.ProductData.TYPE_FLOAT32)
        self.dense1_band = target_product.addBand('Dense1', snappy.ProductData.TYPE_FLOAT32)
        self.misch2_band = target_product.addBand('Misch2', snappy.ProductData.TYPE_FLOAT32)

        # Provide the created target product to the framework so the computeTileStack method can be called
        # properly and the data can be written to disk.
        context.setTargetProduct(target_product)

    def computeTileStack(self, context, target_tiles, target_rectangle):
        # The operator is asked by the framework to provide the data for a rectangle when the data is needed.
        # The required source data for the computation can be retrieved by getSourceTile(...) via the context object.

        # _InputSpec = [
        #     ("b16", float64[:]),     # reflec_1609
        #     ("b2", float64[:]),      # sand-wc_abundance
        #     ("bsum", float64[:]),    # b12 + b13 + b14
        #     ("b19", float64[:]),     # muschelindex
        #     ("b3", float64[:]),      # schatten_abundance
        #     ("b13", float64[:]),     # reflec_561
        #     ("b7", float64[:]),      # flh
        #     ("b15", float64[:]),     # reflec_865
        #     ("b4", float64[:]),      # summary_error
        #     ("b14", float64[:]),     # reflec_655
        #     ("b5", float64[:]),      # steigung_red_nIR
        #     ("b8", float64[:]),      # ndvi
        #     ("b100", float64[:]),    # summary_error
        #     ("b6", float64[:]),      # steigung_nIR_SWIR1
        #     ("b1", float64[:]),      # sand-tr_abundance
        #     ("b12", float64[:]),     # reflec_483
        # ]

        b16_tile = context.getSourceTile(self.band_b16, target_rectangle)
        b2_tile = context.getSourceTile(self.band_b2, target_rectangle)
        b19_tile = context.getSourceTile(self.band_b19, target_rectangle)
        b3_tile = context.getSourceTile(self.band_b3, target_rectangle)
        b13_tile = context.getSourceTile(self.band_b13, target_rectangle)
        b7_tile = context.getSourceTile(self.band_b7, target_rectangle)
        b15_tile = context.getSourceTile(self.band_b15, target_rectangle)
        b4_tile = context.getSourceTile(self.band_b4, target_rectangle)
        b14_tile = context.getSourceTile(self.band_b14, target_rectangle)
        b5_tile = context.getSourceTile(self.band_b5, target_rectangle)
        b8_tile = context.getSourceTile(self.band_b8, target_rectangle)
        b6_tile = context.getSourceTile(self.band_b6, target_rectangle)
        b1_tile = context.getSourceTile(self.band_b1, target_rectangle)
        b12_tile = context.getSourceTile(self.band_b12, target_rectangle)

        # The actual data can be retrieved from the tiles by getSampleFloats(), getSamplesDouble() or getSamplesInt()
        # Values at specific pixel locations can be retrieved for example by first_tile.getSampleFloat(x, y)
        b16_samples = b16_tile.getSamplesFloat()
        b2_samples = b2_tile.getSamplesFloat()
        b19_samples = b19_tile.getSamplesFloat()
        b3_samples = b3_tile.getSamplesFloat()
        b13_samples = b13_tile.getSamplesFloat()
        b7_samples = b7_tile.getSamplesFloat()
        b15_samples = b15_tile.getSamplesFloat()
        b4_samples = b4_tile.getSamplesFloat()
        b14_samples = b14_tile.getSamplesFloat()
        b5_samples = b5_tile.getSamplesFloat()
        b8_samples = b8_tile.getSamplesFloat()
        b6_samples = b6_tile.getSamplesFloat()
        b1_samples = b1_tile.getSamplesFloat()
        b12_samples = b12_tile.getSamplesFloat()

        # Convert the data into numpy data. It is easier and faster to work with as if you use plain python arithmetic
        b16_data = numpy.array(b16_samples, dtype=numpy.float64)
        b2_data = numpy.array(b2_samples, dtype=numpy.float64)
        b19_data = numpy.array(b19_samples, dtype=numpy.float64)
        b3_data = numpy.array(b3_samples, dtype=numpy.float64)
        b13_data = numpy.array(b13_samples, dtype=numpy.float64)
        b7_data = numpy.array(b7_samples, dtype=numpy.float64)
        b15_data = numpy.array(b15_samples, dtype=numpy.float64)
        b4_data = numpy.array(b4_samples, dtype=numpy.float64)
        b14_data = numpy.array(b14_samples, dtype=numpy.float64)
        b5_data = numpy.array(b5_samples, dtype=numpy.float64)
        b8_data = numpy.array(b8_samples, dtype=numpy.float64)
        b6_data = numpy.array(b6_samples, dtype=numpy.float64)
        b1_data = numpy.array(b1_samples, dtype=numpy.float64)
        b12_data = numpy.array(b12_samples, dtype=numpy.float64)

        input = intertidal_flat_classif.Input()
        input.b16 = b16_data
        input.b2 = b2_data
        input.b19 = b19_data
        input.b3 = b3_data
        input.b13 = b13_data
        input.b7 = b7_data
        input.b15 = b15_data
        input.b4 = b4_data
        input.b14 = b14_data
        input.b5 = b5_data
        input.b8 = b8_data
        input.b6 = b6_data
        input.b1 = b1_data
        input.b12 = b12_data

        # Doing the actual computation
        intertidal_flat_classif.apply_rules()

        # _OutputSpec = [
        #     ("Muschel", float64[:]),
        #     ("Schill", float64[:]),
        #     ("Sand", float64[:]),
        #     ("Schlick", float64[:]),
        #     ("Misch", float64[:]),
        #     ("schlick_t", float64[:]),
        #     ("Strand", float64[:]),
        #     ("nodata", float64[:]),
        #     ("Wasser2", float64[:]),
        #     ("Wasser", float64[:]),
        #     ("dense2", float64[:]),
        #     ("dense1", float64[:]),
        #     ("Misch2", float64[:]),
        # ]
        classif_output = intertidal_flat_classif.Output

        # The target tile which shall be filled with data are provided as parameter to this method
        muschel_tile = target_tiles.get(self.muschel_band)
        schill_tile = target_tiles.get(self.schill_band)
        sand_tile = target_tiles.get(self.sand_band)
        schlick_tile = target_tiles.get(self.schlick_band)
        misch_tile = target_tiles.get(self.misch_band)
        schlick_t_tile = target_tiles.get(self.schlick_t_band)
        strand_tile = target_tiles.get(self.strand_band)
        wasser2_tile = target_tiles.get(self.wasser2_band)
        wasser_tile = target_tiles.get(self.wasser_band)
        dense2_tile = target_tiles.get(self.dense2_band)
        dense1_tile = target_tiles.get(self.dense1_band)
        misch2_tile = target_tiles.get(self.misch2_band)

        # Set the result to the target tiles
        muschel_tile.setSamples(classif_output.Muschel)
        schill_tile.setSamples(classif_output.Schill)
        sand_tile.setSamples(classif_output.Sand)
        schlick_tile.setSamples(classif_output.Schlick)
        misch_tile.setSamples(classif_output.Misch)
        schlick_t_tile.setSamples(classif_output.schlick_t)
        strand_tile.setSamples(classif_output.Strand)
        wasser2_tile.setSamples(classif_output.Wasser2)
        wasser_tile.setSamples(classif_output.Wasser)
        dense2_tile.setSamples(classif_output.dense2)
        dense1_tile.setSamples(classif_output.dense1)
        misch2_tile.setSamples(classif_output.Misch2)

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
