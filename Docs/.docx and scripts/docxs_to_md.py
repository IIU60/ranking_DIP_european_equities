import aspose.words as aw
import os

working_doc_fp = r'Docs/.docx and scripts/equities_ranking images.docx'
docs_dir_fp = r'c:\Users\hugo.perezdealbeniz\Documents\GitHub\ranking_DIP_european_equities\Docs'

clean_doc_name = os.path.splitext(os.path.basename(working_doc_fp))[0].lower().replace(' ','_')
saving_dir_name = os.path.join(docs_dir_fp,'Images', clean_doc_name)

if not os.path.exists(saving_dir_name):
    os.makedirs(saving_dir_name)

doc = aw.Document(working_doc_fp)

shapes = doc.get_child_nodes(aw.NodeType.SHAPE, True)

imageIndex = 0   
for shape in shapes:
    shape = shape.as_shape()
    if (shape.has_image):
        
        imageFileName = f"{clean_doc_name}.{str(imageIndex+1).zfill(3)}{aw.FileFormatUtil.image_type_to_extension(shape.image_data.image_type)}"

        shape.image_data.save(os.path.join(saving_dir_name, imageFileName))
        imageIndex += 1