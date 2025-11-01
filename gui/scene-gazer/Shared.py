
import automatey.Utils.TimeUtils as TimeUtils
import automatey.OS.FileUtils as FileUtils
import automatey.Formats.JSON as JSON

import typing
from pprint import pprint
from collections import OrderedDict
import copy

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
        def parseTags(metadata:dict) -> OrderedDict[str, list]:
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
        def unionizeTags(baseTags, extraTags) -> OrderedDict[str, list]:
            '''
            Return the union of two (sets of) tags.
            '''
            resultTags = copy.deepcopy(baseTags)

            # ? Convert 'list' to 'set'.
            for resultTagCategory in resultTags:
                resultTags[resultTagCategory] = set(resultTags[resultTagCategory])

            for extraTagCategory in extraTags:

                if extraTagCategory not in resultTags:
                    resultTags[extraTagCategory] = set(extraTags[extraTagCategory])
                else:
                    resultTags[extraTagCategory] = resultTags[extraTagCategory].union(set(extraTags[extraTagCategory]))

            # ? Sort tag(s) alphabetically.
            # ? ? Sort tag categories.
            resultTags = OrderedDict(sorted(resultTags.items(), key=lambda x: x[0]))
            # ? ? Sort tag categories content.
            for resultTagCategory in resultTags:
                resultTags[resultTagCategory] = list(resultTags[resultTagCategory])
                resultTags[resultTagCategory].sort()

            return resultTags

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

        @staticmethod
        def parseDescription(metadata:dict) -> str:
            '''
            Parses description from metadata.

            Returns `None` if not defined.
            '''
            description = None

            if 'description' in metadata:

                description = metadata['description']
            
            return description

        @staticmethod
        def find(f_target:FileUtils.File) -> dict:
            '''
            Returns `metadata` that corresponds to a specific video file.

            If not available, `None` is returned.
            '''

            metadata = None

            f_metadata = f_target.traverseDirectory('..', '.metadata', f_target.getNameWithoutExtension() + '.json')
            if f_metadata.isExists():
                metadata = JSON.fromFile(f_metadata)
            
            return metadata
