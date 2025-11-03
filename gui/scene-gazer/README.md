
# Overview

`scene-gazer` is a video file viewer and directory explorer.

## Viewer

The viewer renders the video file, and loads metadata information, if existent.

The metadata file must reside under `../VIDEO-FILE-NAME.json` relative to the video file.

## Explorer

The explorer displays the video file hierarchy under the directory, and loads metadata information for each nested file and directory, if existent.

The metadata file must reside under `../FILE-NAME.json` relative to the video file or directory.

## Metadata

*Note:* Only `description` metadata information is supported for directories.

### `tags` 

```
{
    "tags": [
        "Category / Label"
    ]
}
```

### `description` 

```
{
    "description" : [
        [
            "Paragraph-1, Line-1.",
            "Paragraph-1, Line-2.",
            "Paragraph-1, Line-3."
        ],
        [
            "Paragraph-2, Line-1."
            "Paragraph-2, Line-2.",
            "Paragraph-2, Line-3."
        ]
    ]
}
```

```
{
    "description" : [
        "Line-1",
        "Line-2",
        "Line-3"
    ]
}
```

### `chapters` 

```
{
    "chapters": [
        {
            "description": "La-bla!",
            "timestamp": "00:00:00.000"
        }
    ]
}
```

### `highlights` 

```
{
    "highlights": [
        {
            "description": "La-bla!",
            "timestamp": "00:00:00.000"
        }
    ]
}
```

