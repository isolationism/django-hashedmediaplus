
from copy import deepcopy
from django.conf import settings

def compress_settings(request):
    """Expose the COMPRESS_JS and COMPRESS_CSS variables to templates for 
    decoupling"""

    def _addslash(path):
        """Adds a (forward) slash prefix to a passed path; this is safe for
        use in templates because Django templates always use a forward-slash
        regardless of the OS in use"""
        return "/" + path;

    def _loopitems(cdict):
        """Loops over COMPESS_JS and COMPRESS_CSS to add slash prefixes"""
        for k, v in cdict.iteritems():
            for k2, v2 in v.iteritems():
                if k2 == "output_filename":
                    cdict[k][k2] = _addslash(v2)
                if k2 == "source_filenames":
                    cdict[k][k2] = list(v2) # Re-cast tuple as list
                    for i3, v3 in enumerate(v2):
                        cdict[k][k2][i3] = _addslash(v3)
        return cdict
    
    c_js = _loopitems( deepcopy(settings.COMPRESS_JS) )
    c_css = _loopitems( deepcopy(settings.COMPRESS_CSS) )
    return {
        "LOCAL_MEDIA_URL": settings.LOCAL_MEDIA_URL,
        "compress_js": c_js, 
        "compress_css": c_css,
        "compress_enabled": settings.COMPRESS,
        "hashedmedia_enabled": settings.HASHEDMEDIA_ENABLED,
    }
