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

<code>
├── <span style="color: green;"> main.tex </span>
├── <span style="color: green;"> your-custom-commands.tex </span>
├── <span style="color: green;"> classicthesis-config.tex </span>
├── front_back_matter
│   ├── <span style="color: green;"> Abstract.tex </span>
│   ├── <span style="color: green;"> Acknowledgments.tex </span>
│   ├── <span style="color: green;"> Bibliography.tex </span>
│   ├── <span style="color: green;"> Colophon.tex </span>
│   ├── <span style="color: green;"> Contents.tex </span>
│   ├── <span style="color: green;"> Declaration.tex </span>
│   ├── <span style="color: green;"> Dedication.tex </span>
│   ├── <span style="color: green;"> DirtyTitlepage.tex </span>
│   ├── <span style="color: green;"> Publications.tex </span>
│   ├── <span style="color: green;"> Titleback.tex </span>
│   └── <span style="color: green;"> Titlepage.tex </span>
├── appendices
│   └── AppendixA.tex
├── bibs
│   ├── publications.bib
│   └── thesis.bib
├── chapters
│   └── chapter_1.tex
├── figures
│   ├── chapter_1
│   │   ├── guidebook-phd.png
│   │   ├── no-sleep-for-the-wicked.jpg
│   │   ├── scientists.jpeg
│   │   └── start.jpg
│   └── title
│       ├── ratt-logo.png
│       └── rhodes-logo.png
├── snippets
│   └── some-noise.reg
├── <span style="color: red"> classicthesis-arsclassica.sty </span>
├── <span style="color: red"> classicthesis.sty </span>
├── <span style="color: pink"> baskervaldadfstd-bolditalic.otf </span>
├── <span style="color: pink"> baskervaldadfstd-bold.otf </span>
├── <span style="color: pink"> baskervaldadfstd-heavyitalic.otf </span>
├── <span style="color: pink"> baskervaldadfstd-heavy.otf </span>
├── <span style="color: pink"> baskervaldadfstd-italic.otf </span>
└── <span style="color: pink"> baskervaldadfstd-regular.otf  </span>

</code>

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