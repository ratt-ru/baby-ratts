## Usage instructions

To compile this template, use **texlive 2022** on overleaf

Menu > Settings > `Tex Live version 2022`

It takes abit of time to compile with the basic version.But when the time comes and you have access to the
premium version from Oleg, more compile time will be available.

Remember, for faster compile times, one can:
1. Compile the single chapter that is currently being worked on
2. Disable image rendering by setting the draft option of the graphicx package i.e
    - `\usepackage[draft]{graphicx}`

The template directory is ordered as follows:

----

```
+├──main.tex
+├──your-custom-commands.tex
+├──classicthesis-config.tex
├── front_back_matter
+│   ├──Abstract.tex
+│   ├──Acknowledgments.tex
+│   ├──Bibliography.tex
+│   ├──Colophon.tex
+│   ├──Contents.tex
+│   ├──Declaration.tex
+│   ├──Dedication.tex
+│   ├──DirtyTitlepage.tex
+│   ├──Publications.tex
+│   ├──Titleback.tex
+│   └──Titlepage.tex
#├── appendices
#│   └── AppendixA.tex
#├── bibs
#│   ├── publications.bib
#│   └── thesis.bib
#├── chapters
#│   └── chapter_1.tex
#├── figures
#│   ├── chapter_1
#│   │   ├── guidebook-phd.png
#│   │   ├── no-sleep-for-the-wicked.jpg
#│   │   ├── scientists.jpeg
#│   │   └── start.jpg
#│   └── title
#│       ├── ratt-logo.png
#│       └── rhodes-logo.png
#├── snippets
#│   └── some-noise.reg
-├── classicthesis-arsclassica.sty
-├── classicthesis.sty
!├── baskervaldadfstd-bolditalic.otf
!├── baskervaldadfstd-bold.otf
!├── baskervaldadfstd-heavyitalic.otf
!├── baskervaldadfstd-heavy.otf
!├── baskervaldadfstd-italic.otf
!└── baskervaldadfstd-regular.otf 
```

The files in **green** are the *parts of the template* you can and should edit:
- `classicthesis-config.tex`: The various packages imported into the templates, colour declarations etc are in this file. You can add your own imports here
- `your-custom-commands.tex`: As the name suggests, add your custom commands here for easy access. For example, you can declare aliases of your mostly used commands here
- `main.tex`: This is the file that controls everything else. Here's where rendering of certain chapters can be disabled. New chapters to be rendered should also be added here.
- `front_back_matter` directory contains files of different introductory/ finale texts. They're clearly labelled. You can't miss your way.

-------

`appendices / bibs /chapters / figures / snippets`: these are defined by you. You're free to delete and add things as you see fit. These are the contents of your thesis.


The files in the pink (*.Otf) are the fonts used for this thesis, don't touch them and DO NOT DELETE!
The files in red are the template styling files DO NOT TOUCH DO NOT DELETE, unless of course you know what you're doing.


-------
A sample PDF of how the final thesis will look [like is here](./main.pdf)