import streamlit as st
import plotly_express as px
import streamlit_authenticator as stauth  # 
import pandas as pd
import pickle
import json
import datetime
import xlrd
import re
import xlwt
import csv
import time
import openpyxl
from xlwt import Workbook
from pathlib import Path
import scipy.stats as stats
import numpy as np
import matplotlib.pyplot as plt
import base64  # Standard Python Module
import plotly.graph_objects as go
from io import StringIO, BytesIO  # 
from matplotlib import pyplot as plt
from bson.objectid import ObjectId
from datetime import datetime
from os import listdir
from os.path import isfile, join
###################################
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode
from st_aggrid import GridUpdateMode, DataReturnMode
###################################
from streamlit_option_menu import option_menu
###################################
from pymongo import MongoClient
###################################
def main():
        st.set_page_config(page_title="Watts water technologies", page_icon=":bar_chart:", layout="wide")
        st.image(
        "https://th.bing.com/th/id/R.3ca39b52df7b7e082a379e11ba8647a8?rik=w6474wF9boVwTg&riu=http%3a%2f%2fwww.toboaenergy.com%2fwp-content%2fuploads%2f2015%2f01%2fWatts-logo.jpg&ehk=JSEM2%2b8BhyTSa8Vwjzz7IzZ%2flDPUI6Ke5epK3ibSbYI%3d&risl=&pid=ImgRaw&r=0",
        width=100,
        )
        st.title("Watts Industries Tunisia")   
        with st.sidebar:
            selected=option_menu(
            menu_title="Menu",
            options=["Données generiques","Valeurs limites","cp et cpk","gaussienne","top de défaut","taux de défaut en PPM","Pareto de défauts Test","Evolution du défaut","info"],
            )
        c29, c30, c31 = st.columns([1, 6, 1])
        with c30:
           # monRepertoire=r"C:\Users\SIS\OneDrive - enis.tn\Bureau\texte"
           # fichiers = [f for f in listdir(monRepertoire) if isfile(join(monRepertoire, f))]
           # st.write(fichiers)
            uploaded_file = st.sidebar.file_uploader(
                        label="Téléchargez votre fichier Excel. (200 Mo maximum)",
                         type=['csv','txt','xlsx'])
            
            @st.cache(allow_output_mutation=True)
            def load_data(file):
                shows = pd.read_excel(uploaded_file,engine=None)
                return shows
            mergedlist = []
            if uploaded_file is not None:
               
                file_container = st.expander("Vérifiez votre .XLSX téléchargé")
                shows=load_data(uploaded_file)
                 #pd.read_table(uploaded_file,  delimiter="\s+", encoding= 'unicode_escape')
                uploaded_file.seek(0)
                shows=shows.fillna(0)
                nomf=uploaded_file.name
                string=re.sub(".xlsx","",nomf)
                shows['Hour']=pd.to_datetime(shows['Heure'],format='%H:%M:%S').dt.hour
                shows["Week"] = shows['Date'].apply(lambda x: x.strftime("%W"))
                shows['Date']=shows['Date'].apply(lambda x: x.strftime("%d/%m/%y"))
                file_container.write(shows)
            else:
                st.info(
                    f"""
                👆 Téléchargez d'abord un fichier .csv
                """
                )
                st.stop()
      
        def generate_excel_download_link(df):
           # Credit Excel: https://discuss.streamlit.io/t/how-to-add-a-download-excel-csv-function-to-a-button/4474/5
            towrite = BytesIO()
            df.to_excel(towrite, encoding="utf-8", index=False, header=True)  # write to BytesIO buffer
            towrite.seek(0)  # reset pointer
            b64 = base64.b64encode(towrite.read()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_download.xlsx">Download Excel File</a>'
            return st.markdown(href, unsafe_allow_html=True)
        
        with st.form("my_form"):
                col1,col2=st.columns([2,1])
                with col1:
                    produit=st.text_input("code produit")      
                with col2:
                    st.text('Info')
                    button=st.form_submit_button(label='Enregistrer')
                    
        
        client = MongoClient("mongodb://localhost:27017/")
        if selected=="Données generiques":
           
          
            st.header("Données generiques")
            gb = GridOptionsBuilder.from_dataframe(shows)
    # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
            #gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_pagination(enabled=True)
            gb.configure_default_column(editable=True, groupable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
            gridOptions = gb.build()
            st.success(
                 f"""
                💡 Pointe! Maintenez la touche Maj enfoncée lors de la sélection de lignes pour sélectionner plusieurs lignes à la fois !
                """
                )

            response = AgGrid(
            shows,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            theme='fresh'
            )
                
            
            df = pd.DataFrame(response["selected_rows"])
                
            st.header("Résultat:")
            with st.form("my_form2"):
                col1,col2=st.columns([2,1])
                with col1:
                    valeur_max=st.number_input("ecrire la valeur max du temp de cycle")
                with col2:
                    button=st.form_submit_button(label='afficher')
            if button:
                df['Temps cycle'] = df['Temps cycle'].astype(float, errors = 'raise')
                df_mask=df['Status test']=='P'
                filtered_df1 = df[df_mask]
                df_mask1=filtered_df1['Temps cycle']<valeur_max
                filtered_df2 = filtered_df1[df_mask1]
               
                # numeric_columns = list(filtered_df1.select_dtypes(['float', 'int']).columns)
               #  y= st.sidebar.selectbox('X axis', options=numeric_columns)
                total_cols=len(df['Status test'])
                total_colsF=len(df[df['Status test'] =='F'])
                x=((total_colsF/total_cols)*1000000)  
                x=round(x)
                if filtered_df1['Temps machine'] is not None:
                    try:
                        tempc=int(np.round((filtered_df2.describe()['Temps cycle']['mean']),3))
                    except:
                        tempc=0  
                
                if filtered_df2['Temps cycle'] is not None:
                    try:
                        temps=int(np.round((filtered_df1.describe()['Temps machine']['mean']),3))
                    except:
                        temps=0  
                
                tempc=round(tempc)
                temps=round(temps)
                st.write(tempc)
                a=df.iloc[0,0]
                
                b=df.iloc[-1,0]
                
                c=df['Heure'][0]
                d=df.iloc[-1,2]
                e=df.iloc[0,4]
                  #  fig = go.Figure(data=[go.Table(
                   #       header=dict(values=['Date de debut', 'Date de fin','temp de debut','temp de fin','N Produit','N fichier','Taux de defaut PPM','Temp de cycle moyen(s)','Temp machine moyen(s)'],
                        #  line_color='darkslategray',
                        #  fill_color='lightskyblue',
                         #   align='left'),
                     #   cells=dict(values=[a,b,c,d,produit,fichier,x,tempc,temps # 1st column
                     # ], # 2nd column
                     #      line_color='darkslategray',
                     #      fill_color='lightcyan',
                        #   align='left'))
                        #    ])
            #   fig.show()
                 # mo={'Date de debut':[a],'Date de fin':[b],'temp de debut':[c],'temp de fin':[d],'N Produit':[produit],'N°OF':[fichier],'N Banc':e ,'Taux de defaut PPM':[x],
               #  'Temp de cycle moyen(s)':[tempc] ,
               #  'Temp machine moyen(s)':[temps]  
                 #   }
                #  df=pd.DataFrame(data=mo)
                #  st.dataframe(df)
             
                if produit is not None :
                    try:
                        mydatabase = client['donnée_génerique']
                        mycollection = mydatabase[produit]
                        b1={'Date de debut':a,'Date de fin':b,'temp de debut':c,'temp de fin':d,'N Produit':produit,'N fichier':string,'N Banc':e,'Taux de defaut PPM':x,'Temp de cycle moyen(s)':tempc ,'Temp machine moyen(s)':temps}
                        rec = mycollection.insert_one(b1)
                        result=mycollection.find()
                        list_cursor=list(result)
                        df1=pd.DataFrame(list_cursor)
                        df1=df1.astype({"_id": str})
                        st.write(df1)
                        st.subheader('Downloads:')
                        generate_excel_download_link(df1)
                    except:
                        st.error('svp mettre code produit')
                        
        if selected=="Valeurs limites":
            if produit is not None:
                try:
                    mydatabase = client['Valeurs_limites']
                    mycollection = mydatabase[produit]
                    result=mycollection.find()
                    if result is not None:
                        try:
                            list_cursor=list(result)
                            df4=pd.DataFrame(list_cursor)
                            df4=df4.astype({"_id": str})
                            st.write(df4)
                        except:
                            st.write('le tableau est vide ')

                    numeric_columns = list(shows.select_dtypes(['float', 'int']).columns)
                    valeurs = st.radio(
                             "est ce que vous pouvez faire une mise à jour",
                             ('oui', 'non'))
                    with st.form("Valeurs_limites"):
                        col1,col2,col3=st.columns([3,2,1])
                        with col1:
                            lsl1=st.number_input("limite inferieur 1")
                        with col2:
                            usl1=st.number_input("limite superieur 1")  
                        with col3:
                            st.text('Valeurs_limites')
                            a= st.sidebar.selectbox('option1', options=numeric_columns)

                            button=st.form_submit_button(label='Enregistrer')
                    if button:
                        with st.expander("Results"):
                            if valeurs == 'oui':
                                st.write('selctionner votre ligne de mise à jour')
                                mydatabase = client['Valeurs_limites']
                                mycollection = mydatabase[produit]
                                resultm=mycollection.find({'etape':a})
                                if resultm is not None:
                                    try:
                                        ay=mycollection.update_many(
                                                    {'etape':a},
                                                    {
                                                        "$set":{'limite inf':lsl1,
                                                        'limite sup':usl1 }
                                                   } 
                                                )
                                        result5=mycollection.find()
                                        list_cursor3=list(result5)
                                        df8=pd.DataFrame(list_cursor3)
                                        df8=df8.astype({"_id": str})
                                        st.write(df8)
                                    except:
                                        st.error('vous devez ajouter cette etape ')
                                    
                            else:
                                ajout = st.radio(
                                     "est ce que vous pouvez ajouter une ligne",
                                      ('oui', 'non'))
                                if ajout == 'oui':
                                    mydatabase = client['Valeurs_limites']
                                    mycollection = mydatabase[produit]
                                    ac={'etape':a,'limite inf':lsl1,'limite sup':usl1 }
                                    resultay=mycollection.find({'etape':a})
                                    if resultay is  None:
                                         st.write('cette étape est déjà enregistré')

                                    else:
                                        rec = mycollection.insert_one(ac)
                                        st.success('votre étape est ajouté avec success')
                                        result2=mycollection.find()
                                        list_cursor1=list(result2)
                                        df2=pd.DataFrame(list_cursor1)
                                        df2=df2.astype({"_id": str})
                                        st.write(df2)  
                                        
                                else :
                                     st.write('votre valeurs limites sont enregistré')
                except:
                     st.error('Ecrire votre code produit')

        if selected=="gaussienne": 
            
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.header("Gaussienne")
            if produit is not None :
                    try:
                        mydatabase = client['donnée_génerique']
                        mycollection = mydatabase[produit]
                        ma=mycollection.drop()
                    except:
                        st.error('svp mettre le code produit')
                    gb = GridOptionsBuilder.from_dataframe(shows)
            # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
                    gb.configure_pagination(enabled=True)
                    gb.configure_default_column(editable=True, groupable=True)
                    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                    gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
                    gridOptions = gb.build()
                    st.success(
                        f"""
                        💡 Pointe! Maintenez la touche Maj enfoncée lors de la sélection de lignes pour sélectionner plusieurs lignes à la fois !
                    """
                    )

                    response = AgGrid(
                    shows,
                    gridOptions=gridOptions,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    fit_columns_on_grid_load=False,
                    allow_unsafe_jscode=True,
                    theme='blue'
                    )
                    time.sleep(5)

                    df = pd.DataFrame(response["selected_rows"])
                    str1='Courbe gaussienne_CODE_P:'
                    str2=str1+produit
                    numeric_columns = list(df.select_dtypes(['float', 'int']).columns)


                    with st.form("my_form1"):
                        col1,col2=st.columns([2,1])
                        with col1:
                             y= st.sidebar.selectbox('X axis', options=numeric_columns)
                        with col2:
                            st.text('Info')
                            button=st.form_submit_button(label='afficher')
                    if button:
                        with st.expander("Résultat"):
                            database = client['Valeurs_limites']
                            mycollection = database[produit]
                            result=mycollection.find({'etape':y})
                            if result is not None:
                                try:
                                    list_cursor=list(result)
                                    for ani in list_cursor:
                                          lsl=ani['limite inf']
                                    for ani in list_cursor:
                                          usl=ani['limite sup']
                                    df_mask1=df[y]<200
                                    filtered_df2 = df[df_mask1]

                                    # Calculating probability density function (PDF)

                                    fig = px.histogram(filtered_df2[y], x=y,title=str2,text_auto=True)
                                    fig.add_vline(x = lsl, annotation_text="Limite inf", line_width=3, line_dash="dash", line_color="green")
                                    fig.add_vline(x = usl, line_width=3,annotation_text="Limite sup",  line_dash="dash", line_color="red")

                                    fig.show()
                                except:
                                    st.error('svp ecrire les valeurs limites')
                    
                   
                   
                    #generate_html_download_link(plot)
        if selected=="cp et cpk": 
            st.header("CP et CPK")
            mydatabase = client['CP_CPK']
            mycollection = mydatabase[produit]
            result=mycollection.find()
            if result is not None:
                try:
                    list_cursor=list(result)
                    df4=pd.DataFrame(list_cursor)
                    df4=df4.astype({"_id": str})
                    st.write(df4)
                    generate_excel_download_link(df4)
                except:
                    st.write('le tableau est vide ')
            
            mydatabase = client['donnée_génerique']
            mycollection = mydatabase[produit]
            ma=mycollection.drop()
            m=shows.head(30)
            valeurs = st.radio(
                     "est ce que vous voulez faire une mise à jour",
                     ('oui', 'non'))

          
            numeric_columns = list(m.select_dtypes(['float', 'int']).columns)
            with st.form("my_form1"):
                col1,col2=st.columns([2,1])
                with col1:
                     a= st.sidebar.selectbox('X axis', options=numeric_columns)
                with col2:
                    st.text('Cp et Cpk')
                    button=st.form_submit_button(label='calculer')
            if button:
                with st.expander("Résultat"):
                    database = client['Valeurs_limites']
                    mycollection = database[produit]
                    result=mycollection.find({'etape':a})
                    if result is not None:
                        try:
                            list_cursor=list(result)
                            for ani in list_cursor:
                                  lsl=ani['limite inf']
                            for ani in list_cursor:
                                  usl=ani['limite sup']
                            sigma = m[a].std()
                            y = m[a].mean()
                            Cp = (usl - lsl) / (6*sigma)
                            cp=abs(Cp)
                            Cpu = (usl- y) / (3*sigma)
                            Cpl = (y - lsl) / (3*sigma)
                            Cpk = np.min([Cpu, Cpl] )
                            #cpk=abs(Cpk)
                            if Cpk>1.33 :
                                b=("Suffisant")  
                            else:
                                b=("Insuffisant")
                            if valeurs == 'oui':
                                st.write('selctionner votre ligne de mise à jour')

                                mydatabase = client['CP_CPK']
                                mycollection = mydatabase[produit]
                                result=mycollection.find({'etape':a})
                                ay=mycollection.update_many(
                                            {'etape':a},
                                            {
                                                "$set":{'limite inf':lsl,'limite sup':usl,'cp':cp ,'cpk':Cpk,'Résultat':b }
                                            } 
                                        )
                                result5=mycollection.find()
                                list_cursor3=list(result5)
                                df8=pd.DataFrame(list_cursor3)
                                df8=df8.astype({"_id": str})
                                st.write(df8)
                            else:
                                ajout = st.radio(
                                  "est ce que vous voulez ajouter une ligne",
                                     ('oui', 'non'))
                                if ajout == 'oui':
                                        mydatabase = client['CP_CPK']
                                        mycollection = mydatabase[produit]
                                        ac={'etape':a,'limite inf':lsl,'limite sup':usl,'cp':cp ,'cpk':Cpk,'Résultat':b}
                                        resultX=mycollection.find({'etape':a})
                                        if resultX is not None:
                                            rec = mycollection.insert_one(ac)
                                            st.success('Votre ligne est insérée avec succès')
                                            result1=mycollection.find()
                                            list_cursor1=list(result1)
                                            df2=pd.DataFrame(list_cursor1)
                                            df2=df2.astype({"_id": str})
                                            st.write(df2)
                                            st.subheader('Downloads:')
                                            generate_excel_download_link(df2)
                                            
                                        else:
                                            st.write('cette etape est déja calculé')
                                else :
                                    st.write('votre calcul  sont enregistré')
                                    mydatabase = client['CP_CPK']
                                    mycollection = mydatabase[produit]
                                    result=mycollection.find()
                                    list_cursor1=list(result)
                                    df6=pd.DataFrame(list_cursor1)
                                    df6=df2.astype({"_id": str})
                                    st.write(df6)
                                    st.subheader('Downloads:')
                                    generate_excel_download_link(df6)
                        except:
                            st.error("svp mettre les valeurs limites")
            
        

            
            
        if selected=="top de défaut":
            
            st.header("Top de défaut")
            mydatabase = client['donnée_génerique']
            mycollection = mydatabase[produit]
            ma=mycollection.drop()
            st.set_option('deprecation.showPyplotGlobalUse', False)
            df_mask=shows['Status test']=='F'
            filtered_df = shows[df_mask]
            print(filtered_df)
            str1='Top de défaut code produit:'
            str2=str1+produit
            #non_numeric_columns = list(filtered_df.select_dtypes(['object']).columns)
            #columns_to_plot=st.selectbox("select 1 column",non_numeric_columns)
            pie_chart=px.pie((filtered_df['Etape en défaut']).value_counts(),title=str2,names=filtered_df['Etape en défaut'])
            st.plotly_chart(pie_chart)
            st.pyplot()
        if selected=="Pareto de défauts Test": 
            st.header("Pareto de défauts Test")
            str1='Pareto de défauts Test CODE_P:'
            str2=str1+produit
            gb = GridOptionsBuilder.from_dataframe(shows)
    # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
            gb.configure_pagination(enabled=True)
            gb.configure_default_column(editable=True, groupable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
            gridOptions = gb.build()

            st.success(
                f"""
                💡 Pointe! Maintenez la touche Maj enfoncée lors de la sélection de lignes pour sélectionner plusieurs lignes à la fois !
            """
            )

            response = AgGrid(
            shows,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            theme='fresh'
            )
            time.sleep(5)
            df = pd.DataFrame(response["selected_rows"])
            if response is None:
                st.error('faire le filtre')
           
            df_mask=df['Status test']=='F'
            filtered_df = df[df_mask]
            
            st.bar_chart(filtered_df['Etape en défaut'] )
            x=df.count()['Op']
           
            y=filtered_df['Etape en défaut'].value_counts()
            PPM=((y/x)*1000000)
            PPM=round(PPM)
            st.write(round(PPM, 2))
            
            fig = go.Figure()
            #fig = px.bar(
            #filtered_df['Etape en défaut'].value_counts(),
            #template='plotly_white',
            #title=str2
           # )
            fig = px.bar(
            filtered_df,x='Etape en défaut',
            template='plotly_white',
            title=str2
            )
            #fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            
            fig.add_trace(go.Scatter(
                x=filtered_df['Etape en défaut'].value_counts(),
                y=PPM,
                name="PPM",
                yaxis="y3",text=PPM
                ))
            #ffig.update_traces(textposition='top center')
            fig.update_layout(showlegend=True)
            fig.update_layout(
            yaxis3=dict(
            title="PPM",
            titlefont=dict(
            color="#d62728"
            ),
             tickfont=dict(
            color="#d62728"
            ),
            anchor="x",
            overlaying="y",
            side="right"
            ),
            )
            str1='CODE_P:'
            str2=str1+produit+'_'
            str3=str2+'TOP 10 Défauts'
            # Update layout properties
            fig.update_layout(
            title_text=str3,
            width=800,
            )
            
            fig.show()
            st.plotly_chart(fig)
            
        if selected=="Evolution du défaut":
            gb = GridOptionsBuilder.from_dataframe(shows)
    # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
            gb.configure_pagination(enabled=True)
            gb.configure_default_column(editable=True, groupable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
            gridOptions = gb.build()
            st.success(
                f"""
                💡 Pointe! Maintenez la touche Maj enfoncée lors de la sélection de lignes pour sélectionner plusieurs lignes à la fois !
            """
            )

            response = AgGrid(
            shows,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            theme='fresh'
            )
            if produit is not None:
                try:
                    mydatabase = client['donnée_génerique']
                    mycollection = mydatabase[produit]
                    ma=mycollection.drop()
                except:
                    st.error('svp mettre le code produit')
            time.sleep(5)
            df = pd.DataFrame(response["selected_rows"])
            df_mask=df['Status test']=='F'
            filtered_df = df[df_mask]
            df2=filtered_df['Etape en défaut'].drop_duplicates()
            non_numeric_columns = list(df2)
         
            df1=df.groupby(['Date']).count()['Status test']
            df2=df.groupby(["Week"]).count()['Status test']
            with st.form("défaut"):
                 col1,col2=st.columns([2,1])
            with col1:
                columns_to_plot=st.selectbox("select 1 column",non_numeric_columns)
            with col2:
                st.text('affichage')
                page_names=["Evolution du défaut par jour","Evolution du défaut par semaine"]
                page=st.radio('choisir la courbe',page_names)
                button=st.form_submit_button(label='afficher')
            if button:
                with st.expander("Results"):
                    
                    if page=="Evolution du défaut par jour":
                        df_mask1=df['Etape en défaut']==columns_to_plot
                        filtered_df1 =df[df_mask1]
                        
                        str1='Evolution du défaut par jour code produit:'
                        str2=str1+produit
                        st.subheader("Evolution du défaut ")
                        keys = [pair for pair, df in df.groupby(['Date'])]
                        keys= pd.to_datetime(keys, format="%d/%m/%y", errors='ignore')
                        df4=filtered_df1.groupby(['Date','Etape en défaut']).count()['Op']  
                        st.write(df4)
                        
                        df2=(filtered_df.groupby(['Date']))['Etape en défaut'].value_counts()
                        df2 = pd.DataFrame([df2])
                        st.write (df2) 

                            
                            
                        
                        df3=(filtered_df.groupby(['Date'])).count()['Etape en défaut']
                        
                        df6=filtered_df.groupby(['Date']).count()['Op']
                        df6 = pd.DataFrame([df6])
                        st.write(df6)
                      
                        x=np.round(((df4/df3)*1000000))
                      
                        fig = go.Figure()
                        fig = px.bar(
                        x=keys,y=df.groupby(['Date']).count()['Op'],
                        template='plotly_white', text_auto=True,
                        title=str2
                        )
                        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)

                        fig.add_trace(go.Scatter(
                            x=keys,
                            y=df4,
                            name=columns_to_plot,
                            yaxis="y3",text=df4
                            ))
                        fig.update_layout(
                        yaxis3=dict(
                        title="le nombre de défaut",
                        titlefont=dict(
                        color="#d62728"
                        ),
                         tickfont=dict(
                        color="#d62728"
                        ),
                        anchor="x",
                        overlaying="y",
                        side="right"
                        ),
                        )
                        str1='CODE_P:'
                        str2=str1+produit+'_'
                        str3=str2+'Evolution du défaut'
                        # Update layout properties
                        fig.update_layout(
                        title_text=str3,
                        width=800,
                        )

                        fig.show()
                       
                    else:
                        df_mask1=df['Etape en défaut']==columns_to_plot
                        filtered_df1 =df[df_mask1]
                        st.subheader("Evolution du défaut ")
                        keys1 = [pair for pair, df in df.groupby(['Week'])]
                        df9=filtered_df1.groupby(['Week','Etape en défaut']).count()['Op']
                        fig = go.Figure()
                        fig = px.bar(
                        x=keys1,y=df.groupby(['Week']).count()['Op'],
                        template='plotly_white',text_auto=True
                        
                        )
                        

                        fig.add_trace(go.Scatter(
                            x=keys1,
                            y=df9,
                            name=columns_to_plot,
                            yaxis="y3"
                            ))
                        fig.update_layout(
                        yaxis3=dict(
                        title="le nombre de défaut",
                        titlefont=dict(
                        color="#d62728"
                        ),
                         tickfont=dict(
                        color="#d62728"
                        ),
                        anchor="x",
                        overlaying="y",
                        side="right"
                        ),
                        )
                        str1='CODE_P:'
                        str2=str1+produit+'_'
                        str3=str2+'Evolution du défaut'
                        # Update layout properties
                        fig.update_layout(
                        title_text=str3,
                        width=800,
                        )

                        fig.show()
                        
                        
                        fig,ax1 = plt.subplots()
                        
                       
        if selected=="taux de défaut en PPM":
            if produit is not None:
                try:
                    mydatabase = client['donnée_génerique']
                    mycollection = mydatabase[produit]
                    ma=mycollection.drop()
                except:
                    st.error('svp mettre le code produit')
            gb = GridOptionsBuilder.from_dataframe(shows)
    # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
            gb.configure_pagination(enabled=True)
            gb.configure_default_column(editable=True, groupable=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
            gridOptions = gb.build()

            st.success(
                f"""
                💡 Pointe! Maintenez la touche Maj enfoncée lors de la sélection de lignes pour sélectionner plusieurs lignes à la fois !
            """
            )

            response = AgGrid(
            shows,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            theme='fresh'
            )
            
            df = pd.DataFrame(response["selected_rows"])
            st.header("taux de défaut en PPM")
            df['Date']= pd.to_datetime(df['Date'], format="%d/%m/%y", errors='ignore')
            if df['Date'] is not None:
                
                df1=df.groupby(['Date']).count()['Status test']
                st.write(df1)
                df2=df.groupby(["Week"]).count()['Status test']
                df_mask=df['Status test']=='F'
                filtered_df = df[df_mask]
                
                a=filtered_df.groupby(['Date']).count()['Status test']
                
                b=filtered_df.groupby(['Week']).count()['Status test']
                if filtered_df['Status test'] is  None:
                   
                    PPMJ=1000000
                    
                else:
                    PPMJ=round((a)/(df1)*1000000)
                b=round((b)/(df2)*1000000)
                
            
            with st.form("PPM"):
                 col1,col2=st.columns([2,1])
            with col1:
                PPM=st.number_input("Objectif PPM  ")
            
            with col2:
                st.text('PPM')
                page_names=["taux de défaut par jour","taux de défaut par semaine"]
                page=st.radio('choisir la courbe',page_names)
                button=st.form_submit_button(label='afficher')
            if button:
                with st.expander("Résultat"):
                    
                    if page=="taux de défaut par jour":
                        a = a.to_frame()
                        st.write(a)
                        str1='Code P:'+produit+'_PPM Global au test par jour'
                       
                        st.subheader("PPM Global au test")
                        keys = [pair for pair, df in df.groupby(['Date'])]
                        keys= pd.to_datetime(keys, format="%d/%m/%y", errors='ignore')
                        if PPMJ is not None:

                            fig = px.line( df,x=keys, y=PPMJ, title=str1, markers=True,text=PPMJ)
                            fig.update_traces(textposition='top center')
                            fig.add_hline(y = PPM, annotation_text="Objectif PPM", line_width=3, line_dash="dash", line_color="green")
                            fig.show()
                            if PPMJ is not None:
                                size=PPMJ
                            else:
                                size=0
                            fig = px.scatter(df, x=keys, y=PPMJ, title=str1,text=PPMJ,size=size)
                            fig.update_traces(textposition='top center')
                            fig.add_hline(y = PPM, annotation_text="Objectif PPM", line_width=3, line_dash="dash", line_color="green")
                            fig.show()
                        
                    else:
                        str3='Code P:'+produit+'_PPM Global au test par semaine '
                        
                        
                        keys1 = [pair for pair, df in df.groupby(['Week'])]
                        fig = px.line( x=keys1, y=b, title=str3,markers=True,text=b)
                        fig.update_traces(textposition='top center')
                        fig.add_hline(y = PPM, annotation_text="Objectif PPM", line_width=3, line_dash="dash", line_color="green")
                        fig.show()
                        
                        
        if selected=="info":
            st.subheader("réalisé par:Hamed Mariam")
            st.subheader("2021/2022")
            st.subheader("Streamlit")
            
if __name__=='__main__':
    
        main()

