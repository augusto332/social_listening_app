# Importing packages

import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
from app_functions import get_video_title_from_id, get_comments_for_video, get_all_video_ids_from_playlists, busqueda_youtube, get_video_ids_and_titles_from_channel, extract_comments_from_reddit_post, get_last_reddit_posts
import praw
from datetime import datetime
pd.set_option('display.max_colwidth', 50)  # Mostrar solo 50 caracteres


# Sidebar
st.sidebar.title('Sobre Nosotros')

st.sidebar.markdown('Nuestra herramienta está diseñada para tareas de social listening, permitiendo extraer comentarios y discusiones de las redes sociales.')
st.sidebar.markdown('Es ideal para obtener información valiosa sobre las opiniones y sentimientos de distintas audiencias.')

st.sidebar.markdown('---')

fuente = st.sidebar.selectbox(
    "Selecciona la fuente de datos",
    ('Youtube', 'Reddit', 'Twitter')
)

# Seleccionamos fuente de datos
if fuente == 'Youtube':

    st.title('Social Listening - Youtube')

    st.write('\n')

    st.write('YouTube, como fuente de información, permite analizar transcripciones de videos y comentarios de usuarios, obteniendo insights valiosos sobre opinion pública, percepciones y discusiones sobre temas específicos.')

    st.markdown('---')  # Línea horizontal


    # Opciones disponibles
    opcion_seleccionada = st.radio(
        'Selecciona una acción:',
        ('Extraer comentarios de un video específico.', 
        'Extraer comentarios de videos contenidos en una playlist.', 
        'Extraer comentarios de videos que contengan un término de búsqueda especifico en el título.',
        'Extraer comentarios de videos pertenecientes a un canal específico.')
    )

    if opcion_seleccionada == 'Extraer comentarios de un video específico.':
        
        st.markdown('---')
        link = st.text_input("Ingresa un enlace (URL):")

        # Comprobar si se ingresó un enlace
        if link:
            # Mostrar el enlace ingresado
            # Extraemos el video id del link
            pattern_video_id = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
            video_id = re.search(pattern_video_id, link)
            video_id = str(video_id.group(1))

            
            st.write("Enlace ingresado.")

            st.markdown('---')

            if video_id:
                
                api_key = st.text_input("Ingresa tu clave de API de Youtube", type = 'password')


                if api_key:
                    st.write("Clave ingresada.")

                    # Cliente de youtube usando la API
                    youtube = build('youtube', 'v3', developerKey=api_key)

                    # Funcion para obtener comentarios
                    video_comments = get_comments_for_video(youtube,video_id)

                    comments_df = pd.DataFrame(video_comments)
                    comments_df['VideoID'] = str(video_id)
                    comments_df['VideoTitle'] = comments_df['VideoID'].apply(lambda id: get_video_title_from_id(youtube, id))

                    if not comments_df.empty:

                        st.markdown('---')
                        st.write("Dataset finalizado")
                        
                        # Exportar a CSV
                        csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                        st.download_button(
                            label="Descargar CSV",
                            data=csv,
                            file_name='video_comments.csv',
                            mime='text/csv',
                        )

                    else:
                        st.markdown('---')
                        st.write("No se encontraron comentarios para el video seleccionado.")
                    

            else:
                st.markdown('---')
                st.write("Por favor, ingresa una clave.")


    elif opcion_seleccionada == 'Extraer comentarios de videos contenidos en una playlist.':

        st.markdown('---')
        link = st.text_input("Ingresa el enlace de la playlist (URL):")

        if link:
             pattern_playlist_id = pattern_playlist_id = r'[\?&]list=([a-zA-Z0-9_-]+)'
             playlist_id = re.search(pattern_playlist_id, link)
             playlist_id = str(playlist_id.group(1))
             
             # La funcion que se usa a continuacion requiere que sea una lista, 
             # En el futuro esto se puede quitar, o modificar lo anterior para que el input puedan ser varias playlists
             playlist_id = playlist_id.split() 

             st.markdown('---')
             
             api_key = st.text_input("Ingresa tu clave de API de Youtube", type = 'password')
             
             if api_key:
                  st.write("Clave ingresada.")
                  # Cliente de youtube usando la API
                  youtube = build('youtube', 'v3', developerKey=api_key)
                  # Funcion para obtener comentarios

                  video_ids = get_all_video_ids_from_playlists(youtube, playlist_id)
                  video_ids = pd.DataFrame(video_ids)

                  video_ids['VideoTitle'] = video_ids['VideoID'].apply(lambda id: get_video_title_from_id(youtube, id))

                  all_comments = []

                  progress_bar = st.progress(0)
                  progress_text = st.empty()
                  total_videos = len(video_ids)

                  for index, video_id in enumerate(list(video_ids.VideoID)):
                       try:
                        video_comments = get_comments_for_video(youtube, video_id)
                        all_comments.extend(video_comments)
                       except Exception as e:
                        st.write(f"Error al procesar Video ID: {video_id}. Error: {e}")
                        continue
                       
                       # Update progress bar and display current status
                       progress_percentage = (index + 1) / total_videos
                       progress_bar.progress(progress_percentage)
                       progress_text.text(f"Processing video {index + 1} of {total_videos}")
                  
                  # Indicate that the process is complete
                  st.success("Processing complete!")
                       
                  # Create DataFrame
                  comments_df = pd.DataFrame(all_comments)
                  comments_df = pd.merge(comments_df, video_ids, on = 'VideoID' ,how='left')

                  if not comments_df.empty:
                      st.markdown('---')
                      st.write("Dataset finalizado")

                      # CSV
                      csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                      st.download_button(
                            label="Descargar CSV",
                            data=csv,
                            file_name='video_comments.csv',
                            mime='text/csv',
                        )
                  else:
                    st.markdown('---')
                    st.write("No se encontraron comentarios para los videos seleccionados.")
             
             
        

    elif opcion_seleccionada == 'Extraer comentarios de videos que contengan un término de búsqueda especifico en el título.':
        st.markdown('---')
        busqueda = st.text_input("Ingresa el término de búsqueda:")

        if busqueda:
            st.write('Tener en cuenta que se priorizan resultados en lenguaje en español automáticamente.')

            api_key = st.text_input("Ingresa tu clave de API de Youtube", type = 'password')

            if api_key:
             
             # Agregar un slider para seleccionar un rango numérico
             max_results = st.slider('Selecciona la cantidad de videos deseados (1-50)', min_value=1, max_value=50, value=20)

             if st.button('Confirmar Eleccion'):

                video_titles_list, video_ids_list = busqueda_youtube(max_results, busqueda, api_key)

                video_ids = pd.DataFrame({'VideoTitle': video_titles_list, 'VideoID': video_ids_list}) 


                st.write('Videos encontrados: ')
                st.dataframe(video_ids)
                
                st.write('---')
                st.write('Extrayendo comentarios...')
                
                all_comments = []

                progress_bar = st.progress(0)
                progress_text = st.empty()
                total_videos = len(list(video_ids.VideoID))

                # Cliente de youtube usando la API
                youtube = build('youtube', 'v3', developerKey=api_key)

                for index, video_id in enumerate(list(video_ids.VideoID)):
                    try:
                        video_comments = get_comments_for_video(youtube, video_id)
                        all_comments.extend(video_comments)
                    except Exception as e:
                        st.write(f"Error al procesar Video ID: {video_id}. Error: {e}")
                        continue
                    # Update progress bar and display current status
                    progress_percentage = (index + 1) / total_videos
                    progress_bar.progress(progress_percentage)
                    progress_text.text(f"Processing video {index + 1} of {total_videos}")
                    
                # Indicate that the process is complete
                st.success("Processing complete!")
                        
                # Create DataFrame
                comments_df = pd.DataFrame(all_comments)
                comments_df = pd.merge(comments_df, video_ids, on = 'VideoID' ,how='left')

                if not comments_df.empty:
                    st.markdown('---')
                    st.write("Dataset finalizado")

                        # CSV
                    csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name='video_comments.csv',
                                mime='text/csv',
                            )
                else:
                    st.markdown('---')
                    st.write("No se encontraron comentarios para los videos seleccionados.")


    elif opcion_seleccionada == 'Extraer comentarios de videos pertenecientes a un canal específico.':
        st.markdown('---')
        canal = st.text_input("Ingresa el link del canal de Youtube")
        pattern = r"(https://www\.youtube\.com/)(@[\w]+)"
        canal = re.search(pattern, canal)
    
        if canal:
            canal = canal.group(2)
            st.write('Canal: ' + str(canal))
            st.write('---')
            api_key = st.text_input("Ingresa tu clave de API de Youtube", type = 'password')

            if api_key:
                videos = get_video_ids_and_titles_from_channel(canal, api_key)
                videos = pd.DataFrame(videos)
                st.write('Cantidad de videos encontrados: ' + str(len(videos.VideoID)))
                st.write('Muestra de los videos encontrados: ')
                st.dataframe(videos.head())
                st.write('---')

                max_results = st.slider('Selecciona la cantidad de videos deseados', min_value=1, max_value=len(videos.VideoID), value=1)

                if st.button('Confirmar Eleccion'):
                    st.write('Extrayendo comentarios...')

                    videos = videos.head(int(max_results))

                    all_comments = []

                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                    total_videos = len(list(videos.VideoID))

                    # Cliente de youtube usando la API
                    youtube = build('youtube', 'v3', developerKey=api_key)

                    for index, video_id in enumerate(list(videos.VideoID)):
                        try:
                            video_comments = get_comments_for_video(youtube, video_id)
                            all_comments.extend(video_comments)
                        except Exception as e:
                            st.write(f"Error al procesar Video ID: {video_id}. Video número: {index}")
                            st.write(f"Error: {e}")
                            continue
                        # Update progress bar and display current status
                        progress_percentage = (index + 1) / total_videos
                        progress_bar.progress(progress_percentage)
                        progress_text.text(f"Processing video {index + 1} of {total_videos}")
                        
                    # Indicate that the process is complete
                    st.success("Processing complete!")
                            
                    # Create DataFrame
                    comments_df = pd.DataFrame(all_comments)
                    comments_df = pd.merge(comments_df, videos, on = 'VideoID' ,how='left')

                    if not comments_df.empty:
                        st.markdown('---')
                        st.write("Dataset finalizado")

                            # CSV
                        csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                        st.download_button(
                                    label="Descargar CSV",
                                    data=csv,
                                    file_name='video_comments.csv',
                                    mime='text/csv',
                                )
                    else:
                        st.markdown('---')
                        st.write("No se encontraron comentarios para los videos seleccionados.")

        else:
            st.write('No se encontró ningún canal de Youtube en el link ingresado.')



elif fuente == 'Reddit':

    st.title('Social Listening - Reddit')

    st.write('\n')

    st.write('Reddit destaca como plataforma de social listening por sus comunidades temáticas donde se generan discusiones detalladas. Ofrece una visión profunda de las opiniones y problemas que preocupan a los usuarios, facilitando la identificación de tendencias y análisis de las percepciones en temas específicos.')

    st.markdown('---')  # Línea horizontal

    opcion_seleccionada = st.radio(
        'Selecciona una acción:',
        ('Extraer comentarios de un posteo específico.', 
        'Extraer posteos filtrados por palabras clave y sus comentarios, dentro de un subreddit especifico.',
        'Extraer los últimos posteos en los que se mencionen palabras específicas y sus comentarios.')
    )

    st.markdown('---')        

    st.write('Credenciales de la API de Reddit')
    app_name = st.text_input("Ingresa tu nombre de la App creada")
    user_id = st.text_input("Ingresa tu nombre de usuario de Reddit")
    client_id = st.text_input("Ingresa tu ID de cliente (Client ID)", type = 'password')
    client_secret = st.text_input("Ingresa tu ID secreto (Secret ID)", type = 'password')


    # Funciones utiles solo para Reddit
    def fetch_comments_from_url(post_url):
        try:
            # Aplicar la función get_reddit_comments a la URL
            title, content, comment_ids, parent_ids, authors, bodies, is_reply, scores = extract_comments_from_reddit_post(reddit, post_url)

            # Crear un DataFrame con los comentarios extraídos
            return pd.Series({'PostTitle': title,
                              'PostContent': content,
                              'CommentID': comment_ids,
                              'ParentCommentID': parent_ids,
                              'CommentAuthor': authors,
                              'CommentBody': bodies,
                              'IsReply': is_reply,
                              'Score': scores})
        except Exception as e:
            st.write(f"Error extrayendo comentarios del siguiente URL: {post_url} \n {e} ")
            # Devolver None en caso de error
            return pd.Series({'CommentIDs': None,
                              'ParentCommentIDs': None,
                              'CommentAuthors': None,
                              'CommentBodies': None,
                              'IsReplies': None,
                              'CommentScores': None})

    if opcion_seleccionada == 'Extraer comentarios de un posteo específico.':
        
        st.markdown('---')        
        post_url = st.text_input("Ingresa un enlace (URL):")

# Replace these with your credentials
        
        if post_url: 
            reddit = praw.Reddit(
            client_id= client_id,
            client_secret=client_secret,
            user_agent= str(app_name) + " by u/" + str(user_id),  # e.g., "scraper:v1.0 (by u/your_username)"
            check_for_async=False) # It is recommended to use async but we are using sync, so i disable warnings
            # Specify the post URL
            
            title, content, comment_ids, parent_ids, authors, bodies, is_reply, scores = extract_comments_from_reddit_post(reddit , post_url)

            # Create a DataFrame for comments
            comments_df = pd.DataFrame({
                'PostTitle': title,
                'PostContent': content,
                'CommentID': comment_ids,
                'ParentCommentID': parent_ids,
                'CommentAuthor': authors,
                'CommentBody': bodies,
                'IsReply': is_reply,
                'Score': scores})

            if not comments_df.empty:

                            st.markdown('---')
                            st.write("Dataset finalizado.")
                            
                            # Exportar a CSV
                            csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name='video_comments.csv',
                                mime='text/csv')


    elif opcion_seleccionada == 'Extraer posteos filtrados por palabras clave y sus comentarios, dentro de un subreddit especifico.':

        st.markdown('---')
        subreddit_name = st.text_input("Ingresa el subreddit: ")

        # Reddit client
        reddit = praw.Reddit(
            client_id= client_id,
            client_secret=client_secret,
            user_agent= str(app_name) + " by u/" + str(user_id),  # e.g., "scraper:v1.0 (by u/your_username)"
            check_for_async=False) # It is recommended to use async but we are using sync, so i disable warnings

        if subreddit_name:

            subreddit = reddit.subreddit(subreddit_name)

            search_query = st.text_input("Indica la palabra clave para filtrar los posteos: ")
            
            title = []
            score = []
            url = []

            if search_query:

                max_results = st.slider('Selecciona la cantidad de posts deseados (1-50)', min_value=1, max_value=50, value=20)

                if st.button('Confirmar Eleccion'):
                    
                    posts = []

                    for submission in subreddit.search(query=search_query, sort='new',limit = int(max_results)):
                        post_date = datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                        submission.comments.replace_more(limit=0)
                        
                        # Append post and comments data to the list
                        posts.append({
                            "subreddit": subreddit_name,
                            "title": submission.title,
                            "score": submission.score,
                            "url": submission.url,
                            "post_text": submission.selftext,
                            "date_created": post_date
                        })
                    
                    comments_df = pd.DataFrame(posts)

                    st.write('Posteos encontrados:')
                    st.dataframe(comments_df)

                    # Crear un contenedor temporal
                    loading_message = st.empty()

                    # Mostrar un mensaje de carga
                    loading_message.text("Extrayendo comentarios...")
                    
                    comments_df = comments_df.join(comments_df['url'].apply(fetch_comments_from_url))
                    
                    comments_df = comments_df.explode(['CommentID', 'ParentCommentID', 'CommentAuthor', 'CommentBody', 'IsReply', 'Score'])
                    loading_message.empty()

                    if not comments_df.empty:

                            st.markdown('---')
                            st.write("Dataset finalizado.")
                            
                            # Exportar a CSV
                            csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                            st.download_button(
                                label="Descargar CSV",
                                data=csv,
                                file_name='video_comments.csv',
                                mime='text/csv')


    elif opcion_seleccionada == 'Extraer los últimos posteos en los que se mencionen palabras específicas y sus comentarios.':

        st.markdown('---')        
        
        search_query = st.text_input("Indica la palabra clave para filtrar los posteos: ")

        if search_query:

            # Reddit client
            reddit = praw.Reddit(
            client_id= client_id,
            client_secret=client_secret,
            user_agent= str(app_name) + " by u/" + str(user_id),  # e.g., "scraper:v1.0 (by u/your_username)"
            check_for_async=False) # It is recommended to use async but we are using sync, so i disable warnings

            posts = get_last_reddit_posts(reddit ,str(search_query), 100)
            df = pd.DataFrame(posts)

            def convert_utc_to_date(utc_timestamp):
                return datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
            df['created_date'] = df['created_date'].apply(convert_utc_to_date)

            st.write('Posteos encontrados:')
            st.dataframe(df)

            # Crear un contenedor temporal
            loading_message = st.empty()

            # Mostrar un mensaje de carga
            loading_message.text("Extrayendo comentarios...")
                    
            comments_df = df.join(df['url'].apply(fetch_comments_from_url))

            comments_df = comments_df.explode(['CommentID', 'ParentCommentID', 'CommentAuthor', 'CommentBody', 'IsReply', 'Score'])

            loading_message.empty()

            if not comments_df.empty:
                st.markdown('---')
                st.write("Dataset finalizado.")
                            
                # Exportar a CSV
                csv = comments_df.to_csv(index=False, encoding = 'utf-8-sig').encode('utf-8-sig')
                st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='video_comments.csv',
                mime='text/csv')

elif fuente == 'Twitter':

    st.title('Social Listening - Twitter')

    st.write('\n')

    st.write('Twitter es útil para tareas de social listening gracias a sus conversaciones breves y menciones constantes. Permite captar reacciones inmediatas, analizar hashtags populares y monitorear temas de tendencia, proporcionando insights sobre la percepción pública y la respuesta de los usuarios en tiempo real.')

    st.markdown('---')  # Línea horizontal

    st.write('En desarrollo')


st.markdown('---')

st.write('Para consultas, solicitudes o brindar feedback, no dudes en escribirnos a nuestro correo.')
st.write('correo@corre.com')
