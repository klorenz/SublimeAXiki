aXiki is a Xiki Clone
=====================

Why a clone?
------------

- Original Xiki works only under Unix based OS, and not on Windows.  Although
  there are requests which are years old, there is still done no effort to make
  it run on Windows.

- I tried Xiki and it is really great, but I often got tracebacks while trying 
  out features.  Apart from some (impressive!) screencasts documentation is 
  rather poor, at least for me it was hard to find my way through it.  I wanted 
  to have some notes about general syntax, but found nothing.

- My Ruby knowledge is too poor to get Xiki running on Windows quickly, and I 
  loved to have more Xiki features in SublimeText.

- I started with extending SublimeXiki_, but soon there were only little utility
  functions left from original code, so I started an own Package.

- I wanted to use Xiki everywhere.  Especially in Documentations.  So I extended
  Xiki Language a bit to get it easier embedded into reStructured
  Text and Markdown.


.. _SublimeXiki: https://github.com/lunixbochs/SublimeXiki


aXiki Concept
-------------

If you are reading this document in SublimeText, it is time to start Xikiing.

You have to remember only two keyboard shortcuts to get started:

- ``ctrl+enter`` — Open a node

- ``ctrl+shift+enter`` — Re-Open a node and pass nested text as input to 
  corresponding handler.

To start right here, run "aXiki: Enable Xiki for this View" from Command 
Palette.

If you are ready, then hit ``ctrl+enter`` at next line:

- `docs`


