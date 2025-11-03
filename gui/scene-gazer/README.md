
# Overview

`scene-gazer` is a video file viewer and directory explorer.

## Viewer

The viewer renders the video file, and loads metadata information, if existent.

The metadata file must reside under `../VIDEO-FILE-NAME.json` relative to the video file.

## Explorer

The explorer displays the video file hierarchy under the directory, and loads metadata information for each nested file and directory, if existent.

The metadata file must reside under `../FILE-NAME.json` relative to the video file or directory.

## Metadata

```
{
    "tags": [
        "Category / Label"
    ],
    "descr
    "chapters": [
        {
            "description": "La-bla!",
            "timestamp": "00:00:00.000"
        }
    ],
    "highlights": [
        {
            "description": "La-bla!",
            "timestamp": "00:00:00.000"
        }
    ]
}
```

Note: Only `tags` metadata information is supported for directories.
