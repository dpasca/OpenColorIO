
import unittest, os, sys
import PyOpenColorIO as OCIO

import platform
osname = platform.system()

class ConfigTest(unittest.TestCase):

    SIMPLE_PROFILE = """ocio_profile_version: 1

search_path: luts
strictparsing: false
luma: [0.2126, 0.7152, 0.0722]

roles:
  default: raw
  scene_linear: lnh

displays:
  sRGB:
    - !<View> {name: Film1D, colorspace: vd8}
    - !<View> {name: Raw, colorspace: raw}

active_displays: []
active_views: []

colorspaces:
  - !<ColorSpace>
    name: raw
    family: raw
    equalitygroup: ""
    bitdepth: 32f
    description: |
      A raw color space. Conversions to and from this space are no-ops.
      
    isdata: true
    allocation: uniform

  - !<ColorSpace>
    name: lnh
    family: ln
    equalitygroup: ""
    bitdepth: 16f
    description: |
      The show reference space. This is a sensor referred linear
      representation of the scene with primaries that correspond to
      scanned film. 0.18 in this space corresponds to a properly
      exposed 18% grey card.
      
    isdata: false
    allocation: lg2

  - !<ColorSpace>
    name: vd8
    family: vd8
    equalitygroup: ""
    bitdepth: 8ui
    description: |
      how many transforms can we use?
      
    isdata: false
    allocation: uniform
    to_reference: !<GroupTransform>
      children:
        - !<ExponentTransform> {value: [2.2, 2.2, 2.2, 1]}
        - !<MatrixTransform> {matrix: [1, 2, 3, 4, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], offset: [1, 2, 0, 0]}
        - !<CDLTransform> {slope: [0.9, 1, 1], offset: [0.1, 0.3, 0.4], power: [1.1, 1.1, 1.1], sat: 0.9}
"""
    
    def setUp(self):

        osx_hack = ''
        if osname=="Darwin":
            osx_hack = """
// OSX segfault work-around: Force a no-op sampling of the 3D LUT.
texture3D(lut3d, 0.96875 * out_pixel.rgb + 0.015625).rgb;"""

        self.GLSLResult = """
// Generated by OpenColorIO

vec4 pytestocio(in vec4 inPixel, 
    const sampler3D lut3d) 
{
vec4 out_pixel = inPixel; 
out_pixel = out_pixel * mat4(1.0874889, -0.079466686, -0.0080222245, 0., -0.023622228, 1.0316445, -0.0080222245, 0., -0.023622226, -0.079466686, 1.1030889, 0., 0., 0., 0., 1.);
out_pixel = pow(max(out_pixel, vec4(0., 0., 0., 0.)), vec4(0.90909088, 0.90909088, 0.90909088, 1.));
out_pixel = out_pixel * mat4(1.1111112, -2., -3., -4., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.);
out_pixel = vec4(4.688889, -2.3, -0.40000001, -0.) + out_pixel;
out_pixel = pow(max(out_pixel, vec4(0., 0., 0., 0.)), vec4(0.45454544, 0.45454544, 0.45454544, 1.));""" \
 + osx_hack + \
"""
return out_pixel;
}

"""
    
    def test_is_editable(self):
        
        cfg = OCIO.Config().CreateFromStream(self.SIMPLE_PROFILE)
        self.assertEqual(cfg.isEditable(), False)
        cfg = cfg.createEditableCopy()
        self.assertEqual(cfg.isEditable(), True)
        ctx = cfg.getCurrentContext()
        self.assertEqual(ctx.isEditable(), False)
        ctx = ctx.createEditableCopy()
        self.assertEqual(ctx.isEditable(), True)
        ctx.setEnvironmentMode(OCIO.Constants.ENV_ENVIRONMENT_LOAD_ALL)
    
    def test_interface(self):
        
        _cfg = OCIO.Config().CreateFromStream(self.SIMPLE_PROFILE)
        _cfge = _cfg.createEditableCopy()
        _cfge.clearEnvironmentVars()
        self.assertEqual(0, _cfge.getNumEnvironmentVars())
        _cfge.addEnvironmentVar("FOO", "test1")
        _cfge.addEnvironmentVar("FOO2", "test2${FOO}")
        self.assertEqual(2, _cfge.getNumEnvironmentVars())
        self.assertEqual("FOO", _cfge.getEnvironmentVarNameByIndex(0))
        self.assertEqual("FOO2", _cfge.getEnvironmentVarNameByIndex(1))
        self.assertEqual("test1", _cfge.getEnvironmentVarDefault("FOO"))
        self.assertEqual("test2${FOO}", _cfge.getEnvironmentVarDefault("FOO2"))
        self.assertEqual("test2test1", _cfge.getCurrentContext().resolveStringVar("${FOO2}"))
        self.assertEqual({'FOO': 'test1', 'FOO2': 'test2${FOO}'}, _cfge.getEnvironmentVarDefaults())
        _cfge.clearEnvironmentVars()
        self.assertEqual(0, _cfge.getNumEnvironmentVars())
        self.assertEqual("luts", _cfge.getSearchPath())
        _cfge.setSearchPath("otherdir")
        self.assertEqual("otherdir", _cfge.getSearchPath())
        _cfge.sanityCheck()
        _cfge.setDescription("testdesc")
        self.assertEqual("testdesc", _cfge.getDescription())
        self.assertEqual(self.SIMPLE_PROFILE, _cfg.serialize())
        #self.assertEqual("$07d1fb1509eeae1837825fd4242f8a69:$885ad1683add38a11f7bbe34e8bf9ac0",
        #                _cfg.getCacheID())
        con = _cfg.getCurrentContext()
        self.assertNotEqual(0, con.getNumStringVars())
        #self.assertEqual("", _cfg.getCacheID(con))
        #self.assertEqual("", _cfge.getWorkingDir())
        _cfge.setWorkingDir("/foobar")
        self.assertEqual("/foobar", _cfge.getWorkingDir())
        self.assertEqual(3, _cfge.getNumColorSpaces())
        self.assertEqual("lnh", _cfge.getColorSpaceNameByIndex(1))
        lnh = _cfge.getColorSpace("lnh")
        self.assertEqual("ln", lnh.getFamily())
        self.assertEqual(0, _cfge.getIndexForColorSpace("foobar"))
        cs = OCIO.ColorSpace()
        cs.setName("blah")
        _cfge.addColorSpace(cs)
        self.assertEqual(3, _cfge.getIndexForColorSpace("blah"))
        #_cfge.clearColorSpaces()
        #_cfge.parseColorSpaceFromString("foo")
        self.assertEqual(False, _cfg.isStrictParsingEnabled())
        _cfge.setStrictParsingEnabled(True)
        self.assertEqual(True, _cfge.isStrictParsingEnabled())
        self.assertEqual(2, _cfge.getNumRoles())
        self.assertEqual(False, _cfg.hasRole("foo")) 
        _cfge.setRole("foo", "vd8")
        self.assertEqual(3, _cfge.getNumRoles())
        self.assertEqual(True, _cfge.hasRole("foo"))
        self.assertEqual("foo", _cfge.getRoleName(1))
        self.assertEqual("sRGB", _cfge.getDefaultDisplay())
        self.assertEqual(1, _cfge.getNumDisplays())
        self.assertEqual("sRGB", _cfge.getDisplay(0))
        self.assertEqual("Film1D", _cfge.getDefaultView("sRGB"))
        self.assertEqual(2, _cfge.getNumViews("sRGB"))
        self.assertEqual("Raw", _cfge.getView("sRGB", 1))
        self.assertEqual("vd8", _cfge.getDisplayColorSpaceName("sRGB", "Film1D"))
        self.assertEqual("", _cfg.getDisplayLooks("sRGB", "Film1D"))
        _cfge.addDisplay("foo", "bar", "foo", "wee")
        _cfge.clearDisplays()
        _cfge.setActiveDisplays("sRGB")
        self.assertEqual("sRGB", _cfge.getActiveDisplays())
        _cfge.setActiveViews("Film1D")
        self.assertEqual("Film1D", _cfge.getActiveViews())
        luma = _cfge.getDefaultLumaCoefs()
        self.assertAlmostEqual(0.2126, luma[0], delta=1e-8)
        _cfge.setDefaultLumaCoefs([0.1, 0.2, 0.3])
        tnewluma = _cfge.getDefaultLumaCoefs()
        self.assertAlmostEqual(0.1, tnewluma[0], delta=1e-8)
        self.assertEqual(0, _cfge.getNumLooks())
        lk = OCIO.Look()
        lk.setName("coollook")
        lk.setProcessSpace("somespace")
        et = OCIO.ExponentTransform()
        et.setValue([0.1, 0.2, 0.3, 0.4])
        lk.setTransform(et)
        iet = OCIO.ExponentTransform()
        iet.setValue([-0.1, -0.2, -0.3, -0.4])
        lk.setInverseTransform(iet)
        _cfge.addLook(lk)
        self.assertEqual(1, _cfge.getNumLooks())
        self.assertEqual("coollook", _cfge.getLookNameByIndex(0))
        glk = _cfge.getLook("coollook")
        self.assertEqual("somespace", glk.getProcessSpace())
        _cfge.clearLooks()
        self.assertEqual(0, _cfge.getNumLooks())
        
        #getProcessor(context, srcColorSpace, dstColorSpace)
        #getProcessor(context, srcName,dstName);
        #getProcessor(transform);
        #getProcessor(transform, direction);
        #getProcessor(context, transform, direction);
        
        _proc = _cfg.getProcessor("lnh", "vd8")
        self.assertEqual(False, _proc.isNoOp())
        self.assertEqual(True, _proc.hasChannelCrosstalk())
        
        #float packedpix[] = new float[]{0.48f, 0.18f, 0.9f, 1.0f,
        #                                0.48f, 0.18f, 0.18f, 1.0f,
        #                                0.48f, 0.18f, 0.18f, 1.0f,
        #                                0.48f, 0.18f, 0.18f, 1.0f };
        #FloatBuffer buf = ByteBuffer.allocateDirect(2 * 2 * 4 * Float.SIZE / 8).asFloatBuffer();
        #buf.put(packedpix);
        #PackedImageDesc foo = new PackedImageDesc(buf, 2, 2, 4);
        #_proc.apply(foo);
        #FloatBuffer wee = foo.getData();
        #self.assertEqual(-2.4307251581696764E-35f, wee.get(2), 1e-8);
        
        # TODO: these should work in-place
        rgbfoo = _proc.applyRGB([0.48, 0.18, 0.18])
        self.assertAlmostEqual(1.9351077, rgbfoo[0], delta=1e-7);
        # TODO: these should work in-place
        rgbafoo = _proc.applyRGBA([0.48, 0.18, 0.18, 1.0])
        self.assertAlmostEqual(1.0, rgbafoo[3], delta=1e-8)
        #self.assertEqual("$a92ef63abd9edf61ad5a7855da064648", _proc.getCpuCacheID())
        
        _cfge.clearSearchPaths()
        self.assertEqual(0, _cfge.getNumSearchPaths())
        _cfge.addSearchPath("First/ Path")
        self.assertEqual(1, _cfge.getNumSearchPaths())
        _cfge.addSearchPath("D:\\Second\\Path\\")
        self.assertEqual(2, _cfge.getNumSearchPaths())
        self.assertEqual("First/ Path", _cfge.getSearchPathByIndex(0))
        self.assertEqual("D:\\Second\\Path\\", _cfge.getSearchPathByIndex(1))

        del _cfge
        del _cfg
