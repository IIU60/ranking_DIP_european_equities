import os
os.chdir('Docs/Images/equities_ranking_images')
for filename in os.listdir(os.getcwd())[::-1]:
    old_index = int(filename.split('.')[1])
    if old_index >= 11:
        new_index=1+old_index
    else:
        new_index=old_index
    new_name = filename.replace(str(old_index),str(new_index))
    os.rename(filename,new_name)
    #print(filename,new_name)
