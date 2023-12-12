import lxml.etree as ET
import pandas as pd
import os 

df = pd.read_excel(r"C:\Users\Christopher\Downloads\meta\Downloads_AutoClass.xlsx")
dir = r"G:\My Drive\Documents\opex_manifest_generator\metadata"
for file in os.listdir(dir):
    if file.endswith('.xml'):
        path = os.path.join(dir,file)
        xml_file = ET.parse(path)
        col_list = df.columns.values.tolist()
        #print(col_list) 
        root_elem = ET.QName(xml_file.find('.'))
        root_elem_ln = root_elem.localname
        root_elem_ns = root_elem.namespace
        elems_list = []
        for e in xml_file.findall('.//'):
            elem_path = xml_file.getelementpath(e)            
            elem = ET.QName(e)
            elem_ln = elem.localname
            elem_ns = elem.namespace
            elem_lpath = elem_path.replace(f"{{{elem_ns}}}",root_elem_ln + ":")
            elems_list.append({"Name":root_elem_ln + ":" + elem_ln,"Namespace":elem_ns,"Path":elem_lpath})
        list_xml = []

        for elem_dict in elems_list:
            if elem_dict.get('Name') in col_list or elem_dict.get('Path') in col_list:
                list_xml.append({"Name":elem_dict.get('Name'),"Namespace":elem_dict.get('Namespace'),"Path":elem_dict.get('Path')})
        
        if len(list_xml):
            for fn in df['FullName'].values.tolist():
                idx = df.index[df['FullName'] == fn]
                xml_new = xml_file
                for elem_dict in list_xml:
                    name = elem_dict.get('Name')
                    path = elem_dict.get('Path')
                    ns = elem_dict.get('Namespace')
                    if path.count('/'):
                        val = df.loc[idx,path].values[0]
                        if str(val) == "nan": val = ""
                        n = path.replace(root_elem_ln + ":", f"{{{ns}}}")
                        elem = xml_new.find(f'//{n}')
                        elem.text = str(val)
                    else:
                        val = df.loc[idx,name].values[0]
                        if str(val) == "nan": val = ""
                        n = name.split(':')[-1]
                        elem = xml_new.find(f'//{{{ns}}}{n}')
                        elem.text = str(val)
                        print(val)
                print(ET.tostring(xml_new))
                    