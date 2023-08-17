# import os
# import signal
# import logging

# class BackgroundThreadFactory:
#     @staticmethod
#     def create(thread_type: str, **kwargs) -> BackgroundThread:
#         def switch(thread_type):
#             if thread_type == "weatherSampling":
#                 return weatherSampler(**kwargs)
#             if thread_type == "takePicture":
#                 return takeNewPhoto(**kwargs)
#             elif thread_type == "updateWeather":
#                 return updateWeather(**kwargs)
                
#             raise NotImplementedError('Specified thread type is not implemented.')

#         return switch(thread_type)

# def startThread(name, **kwargs):
#     weather_sampling_thread = BackgroundThreadFactory.create(name, **kwargs)

#     # this condition is needed to prevent creating duplicated thread in Flask debug mode
#     if not (kwargs["app"].debug or os.environ.get('FLASK_ENV') == 'development') or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#         weather_sampling_thread.start()

#         original_handler = signal.getsignal(signal.SIGINT)

#         def sigint_handler(signum, frame):
#             weather_sampling_thread.stop()

#             # wait until thread is finished
#             if weather_sampling_thread.is_alive():
#                 weather_sampling_thread.join()

#             original_handler(signum, frame)

#         try:
#             signal.signal(signal.SIGINT, sigint_handler)
#         except ValueError as e:
#             logging.error(f'{e}. Continuing execution...')