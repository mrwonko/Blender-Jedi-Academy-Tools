PY_FILES = __init__.py mod_reload.py casts.py error_types.py JAAseExport.py JAAseImport.py JAFilesystem.py JAG2AnimationCFG.py JAG2Constants.py JAG2GLA.py JAG2GLM.py JAG2Math.py JAG2Operators.py JAG2Panels.py JAG2Scene.py JAMaterialmanager.py JAMd3Encode.py JAMd3Export.py JAPatchExport.py JARoffExport.py JARoffImport.py JAStringhelper.py MrwProfiler.py

ZIP_CONTENTS = $(PY_FILES) jediacademy_plugins_readme.txt

.PHONY: all

all: jediacademy.zip jediacademy_plugins_doc.pdf

build/jediacademy.zip: $(ZIP_CONTENTS)
# we must first create the desired directory structure for the zip,
# i.e. the top-level "jediacademy" folder
	mkdir -p build/jediacademy
	cp $(ZIP_CONTENTS) build/jediacademy
	(cd build; zip -r jediacademy.zip jediacademy)

build/jediacademy_plugins_doc.pdf: jediacademy_plugins_doc.tex
	mkdir -p build
	pdflatex --output-directory=build jediacademy_plugins_doc.tex
