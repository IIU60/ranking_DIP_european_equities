import aspose.words as aw
import os

working_doc_fp = r'descarga de datos images.docx'
#working_doc_fp = r'descarga de datos truncated.docx'
#working_doc_fp = r'Documentacion descarga de datos eikon.docx'
#working_doc_fp = r'Documentacion equities ranking platform.docx'

clean_doc_name = working_doc_fp.split('.')[0].replace(' ','_')

docs_dir_fp = r'c:\Users\hugo.perezdealbeniz\Documents\GitHub\ranking_DIP_european_equities\Docs'
saving_dir_name = os.path.join(docs_dir_fp,'Images', clean_doc_name)

try:
    os.mkdir(docs_dir_fp+'/Images')
except FileExistsError:
    try:
        os.mkdir(saving_dir_name)
    except FileExistsError:
        pass

doc = aw.Document(working_doc_fp)

shapes = doc.get_child_nodes(aw.NodeType.SHAPE, True)

imageIndex = 0   
for shape in shapes:
    shape = shape.as_shape()
    if (shape.has_image):
        
        imageFileName = f"{clean_doc_name}.{str(imageIndex+1).zfill(3)}{aw.FileFormatUtil.image_type_to_extension(shape.image_data.image_type)}"

        shape.image_data.save(os.path.join(saving_dir_name, imageFileName))
        imageIndex += 1