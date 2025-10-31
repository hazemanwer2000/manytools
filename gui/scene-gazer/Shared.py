
import automatey.Utils.TimeUtils as TimeUtils

import typing
from pprint import pprint
from collections import OrderedDict

class Utils:

    class Metadata:

        class Tag:

            @staticmethod
            def construct(category:str, label:str) -> str:
                '''
                Constructs `tag` from `category` and `label`.
                '''

                return f"{category} / {label}"
            
            @staticmethod
            def split(tag) -> str:
                '''
                Splits `tag` into `(category, label)`.
                '''
                
                tagCategory, tagLabel = tag.split('/')
                tagLabel = tagLabel.strip()
                tagCategory = tagCategory.strip()

                return (tagCategory, tagLabel)

        @staticmethod
        def parseTags(metadata:dict) -> typing.List[str]:
            '''
            Parses tag(s) from metadata.

            Returns `None` if not defined.
            '''
            
            result = None

            if 'tags' in metadata:
                
                result = OrderedDict()
                
                # ? Parse tag(s).
                for tag in metadata['tags']:                    
                    
                    tagCategory, tagLabel = Utils.Metadata.Tag.split(tag)
                    
                    if tagCategory not in result:
                        result[tagCategory] = set()
                    
                    result[tagCategory].add(tagLabel)
                
                # ? Sort tag(s) alphabetically.
                # ? ? Sort tag categories.
                result = OrderedDict(sorted(result.items(), key=lambda x: x[0]))
                # ? ? Sort tag categories content.
                for key in result:
                    result[key] = list(result[key])
                    result[key].sort()

            return result
        
        @staticmethod
        def parseChapters(metadata:dict) -> typing.List[str]:
            '''
            Parses chapter(s) from metadata.

            Returns `None` if not defined.
            '''

            chapters = None

            if 'chapters' in metadata:

                chapters = []

                # ? For each chapter (...)
                for rawChapter in metadata['chapters']:

                    chapter = {}
                    chapter['description'] = str(rawChapter['description'])
                    chapter['timestamp'] = TimeUtils.Time.createFromString(rawChapter['timestamp'])

                    chapters.append(chapter)

                # ? Sort.
                chapters.sort(key=lambda chapter: chapter['timestamp'])

                # ? Add 'index' field.
                for idx, chapter in enumerate(chapters):
                    chapter['index'] = idx + 1
            
            return chapters
        
        @staticmethod
        def parseHighlights(metadata:dict) -> typing.List[str]:
            '''
            Parses highlights(s) from metadata.

            Returns `None` if not defined.
            '''
            highlights = None

            if 'highlights' in metadata:

                highlights = []

                for rawHighlight in metadata['highlights']:

                    highlight = {}
                    highlight['description'] = str(rawHighlight['description'])
                    highlight['timestamp'] = TimeUtils.Time.createFromString(rawHighlight['timestamp'])

                    highlights.append(highlight)
            
            return highlights
