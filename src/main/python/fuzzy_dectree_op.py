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

        self.first_band = source_product.getBandAt(0)

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
        self.target_band = target_product.addBand('target_band', snappy.ProductData.TYPE_FLOAT32)
        self.target_band.setDescription('TODO')
        self.target_band.setNoDataValue(Float.NaN)
        self.target_band.setNoDataValueUsed(True)

        # Provide the created target product to the framework so the computeTileStack method can be called
        # properly and the data can be written to disk.
        context.setTargetProduct(target_product)

    def computeTileStack(self, context, target_tiles, target_rectangle):
        # The operator is asked by the framework to provide the data for a rectangle when the data is needed.
        # The required source data for the computation can be retrieved by getSourceTile(...) via the context object.
        first_tile = context.getSourceTile(self.first_band, target_rectangle)

        # The actual data can be retrieved from the tiles by getSampleFloats(), getSamplesDouble() or getSamplesInt()
        first_samples = first_tile.getSamplesFloat()
        # Values at specific pixel locations can be retrieved for example by first_tile.getSampleFloat(x, y)

        # Convert the data into numpy data. It is easier and faster to work with as if you use plain python arithmetic
        first_data = numpy.array(first_samples, dtype=numpy.float32)
        # Doing the actual computation
        result = self.algo.compute(first_data)

        # The target tile which shall be filled with data are provided as parameter to this method
        result_tile = target_tiles.get(self.target_band)

        # Set the result to the target tiles
        result_tile.setSamples(result)

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
