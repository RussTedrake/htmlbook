
// Definitions for mathjax
var mathjax_setup = `
<div style="display:none" id="mathjax_setup"> 
  \\[
  \\newcommand{\\pd}[2]{\\frac{\\partial #1}{\\partial #2}}
  \\newcommand{\\bc}{{\\bf c}}
  \\newcommand{\\bg}{{\\bf g}}
  \\newcommand{\\bh}{{\\bf h}}
  \\newcommand{\\bq}{{\\bf q}}
  \\newcommand{\\bv}{{\\bf v}}
  \\newcommand{\\bx}{{\\bf x}}
  \\newcommand{\\by}{{\\bf y}}
  \\newcommand{\\bu}{{\\bf u}}
  \\newcommand{\\bw}{{\\bf w}}
  \\newcommand{\\bz}{{\\bf z}}
  \\newcommand{\\bA}{{\\bf A}}
  \\newcommand{\\bB}{{\\bf B}}
  \\newcommand{\\bC}{{\\bf C}}
  \\newcommand{\\bH}{{\\bf H}}
  \\newcommand{\\bI}{{\\bf I}}
  \\newcommand{\\bJ}{{\\bf J}}
  \\newcommand{\\bK}{{\\bf K}}
  \\newcommand{\\bM}{{\\bf M}}
  \\newcommand{\\bQ}{{\\bf Q}}
  \\newcommand{\\bR}{{\\bf R}}
  \\newcommand{\\bT}{{\\bf T}}
  \\newcommand{\\balpha}{{\\bf \\alpha}}
  \\newcommand{\\bbeta}{{\\bf \\beta}}
  \\newcommand{\\blambda}{{\\bf \\lambda}}
  \\newcommand{\\btau}{{\\bf \\tau}}
  \\newcommand{\\bphi}{{\\bf \\phi}}
  \\newcommand{\\bPhi}{{\\bf \\Phi}}
  \\newcommand{\\bpi}{{\\bf \\pi}}
  \\newcommand{\\bpsi}{{\\bf \\psi}}
  \\newcommand{\\bPsi}{{\\bf \\Psi}}
  \\newcommand{\\avg}[1]{E\\left[ #1 \\right]}
  \\newcommand{\\subjto}{\\textrm{subject to}}
  \\newcommand{\\minimize}{\\operatorname{\\textrm{minimize}}}
  \\newcommand{\\maximize}{\\operatorname{\\textrm{maximize}}}
  \\DeclareMathOperator*{\\find}{find}
  \\newcommand{\\argmax}{\\operatorname{\\textrm{argmax}}}
  \\newcommand{\\argmin}{\\operatorname{\\textrm{argmin}}}
  \\newcommand{\\sgn}{\\operatorname{\\textrm{sgn}}}
  \\newcommand{\\trace}{\\operatorname{\\textrm{tr}}}
  \\newcommand{\\sos}{\\text{ is SOS}}
  \\]
</div>

<div id="debug_output"></div>
`;

function setPlatform() {
  platform = 'bionic';
  if (navigator.appVersion.indexOf("Mac")>=0) { platform = 'mac'; }

  function hide(items) { for (let item of items) { item.style.display = "none"; } }
  function show(items) { for (let item of items) { item.style.display = "inline"; } }

  hide(document.getElementsByClassName("mac"));
  hide(document.getElementsByClassName("bionic"));

  show(document.getElementsByClassName(platform));
}

function customTags() {
  // We cannot add a link via CSS, so do it here instead.
  var drakeTags = document.getElementsByTagName('drake');
  for (j = 0; j < drakeTags.length; j++) {
      drakeTags[j].innerHTML =
      '<a style="font-variant:small-caps; text-decoration:none;" href="http://drake.mit.edu">Drake</a>';
  }

  var bib = new Map();

  var elibTags = document.getElementsByTagName('elib');
  for (i = 0; i < elibTags.length; i++) {
    var c = elibTags[i].innerHTML;
    var str = "";
    var index;
    c.split("+").forEach(function(b) {
      if (bib.has(b)) {
        index = bib.get(b);
      } else {
        index = bib.size+1;
        bib.set(b, index);
      }
      if (str.length > 0) {
        str += ", ";
      }
      str += '<a target="_blank" href="http://groups.csail.mit.edu/locomotion/elib.cgi?b=' + b + '">' + index + '</a>';
    });
    elibTags[i].innerHTML = '[' + str + ']';
  }
}

// This is to maintain backwards compatibility (for now)
function forwardOldChapterLink() {
  function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
      results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
  }

  var chapter = getParameterByName("chapter");
  if (chapter) {
    var hash = window.location.hash.substr(1);
    if (hash) {
      window.location = chapter + ".html" + "#" + hash;
    } else {
      window.location = chapter + ".html";
    }
  }
}

function loadChapter(project)  {
  var url = window.location.pathname;
  var filename = url.substring(url.lastIndexOf('/')+1);
  var chapter_id = filename.slice(0, -5);

  var chapter = document.getElementsByTagName("chapter")[0];

  chapter.innerHTML = mathjax_setup + chapter.innerHTML;

  // Make sure all sections have ids and links.
  var sections = chapter.getElementsByTagName("section");
  for (j=0; j<sections.length; j++) {
      if (!sections[j].id) {
          sections[j].id = "section" + (j+1);
      }
      sections[j].getElementsByTagName("h1")[0].innerHTML = "<a href=#" + sections[j].id + ">" + sections[j].getElementsByTagName("h1")[0].innerHTML + "</a>";
  }

  // Make sure all examples have ids and links.
  var examples = chapter.getElementsByTagName("example");
  for (j=0; j<examples.length; j++) {
      if (!examples[j].id) {
          examples[j].id = "example" + (j+1);
      }
      examples[j].getElementsByTagName("h1")[0].innerHTML = "<a href=#" + examples[j].id + ">" + examples[j].getElementsByTagName("h1")[0].innerHTML + "</a>";
  }

  var codeTags = chapter.getElementsByTagName('pysrcinclude');
  for (j = 0; j < codeTags.length; j++) {
      var file = project + '/' + codeTags[j].innerHTML;
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = ( function (j) { return function() {
          if (this.readyState == 4 && this.status == 200) {
              var text = hljs.highlight('python',this.responseText,true)
              codeTags[j].innerHTML =
              '<sidenote><a style="font-size:8pt; margin-left:50%" target="scratchpad" href="https://colab.research.google.com/github/RussTedrake/underactuated/blob/master/scripts/colab_scratchpad.ipynb">' +
              'Colab scratchpad</a></sidenote>';
              codeTags[j].innerHTML +=
              '<div><pre><code class="python">'+text.value+'</code></pre></div>';
          }
      } })(j);
      xhttp.overrideMimeType('text/plain');
      xhttp.open('GET', file, true);
      // note: only works for files in or below current directory http://jquery-howto.blogspot.com/2008/12/access-to-restricted-uri-denied-code.html
      xhttp.send();
  }

  var pysrcTags = chapter.getElementsByTagName('pysrc');
  for (j = 0; j < pysrcTags.length; j++) {
      var file = pysrcTags[j].innerHTML;
      var tmp =
      '<p><pre style="margin-left:6px; display:inline"><code>python3 <a target="' + file +'" href="' + project + '/'+ file + '">' + file + '</a>';
      if (pysrcTags[j].hasAttribute("args")) {
          tmp += ' '+ pysrcTags[j].getAttribute("args");
      }
      pysrcTags[j].innerHTML = tmp + '</code></pre>';
      pysrcTags[j].innerHTML +=
      '<sidenote><a style="font-size:8pt; margin-left:50%" target="scratchpad" href="https://colab.research.google.com/github/RussTedrake/underactuated/blob/master/scripts/colab_scratchpad.ipynb">' +
      'Colab scratchpad</a></sidenote></p>';
  }

  var jupyterTags = chapter.getElementsByTagName('jupyter');
  for (j = 0; j < jupyterTags.length; j++) {
      var file = jupyterTags[j].innerHTML;
      binder_path = file.replace(/\//g,"%2F")
      text = '<p style="text-align:center"> Open <a target="' + file + '_github" href="https://github.com/RussTedrake/underactuated/blob/master/' + file + '">notebook</a>';
      if (!jupyterTags[j].hasAttribute("no_binder") || !jupyterTags[j].hasAttribute("no_colab")) {
        text += ' with ';
      }
      if (!jupyterTags[j].hasAttribute("no_binder")) {
        text += ' <a target="' + file + '_binder" href="https://mybinder.org/v2/gh/RussTedrake/' + project + '/master?filepath=' + binder_path + '">\n' + '<img style="vertical-align:bottom" src="https://mybinder.org/badge_logo.svg" alt="Open in Binder"/></a>';
        if (!jupyterTags[j].hasAttribute("no_colab")) {
          text += ' or ';
        }
      }
      if (!jupyterTags[j].hasAttribute("no_colab")) {
        text += '<a target="' + file + '_colab" href="https://colab.research.google.com/github/RussTedrake/' + project + '/blob/master/' + file + '">\n' +
        '  <img style="vertical-align:bottom" src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>';
      }
      jupyterTags[j].innerHTML = text + ' <span style="display:inline;font-size:x-small">(<a href="?chapter=drake">more info</a>)</span></p>';
  }

  var exerciseTags = chapter.getElementsByTagName('exercise');
  for (j = 0; j < exerciseTags.length; j++) {
      var name = exerciseTags[j].getElementsByTagName("h1")[0].innerHTML;
      if (name) {
          exerciseTags[j].getElementsByTagName("h1")[0].innerHTML = "(" + name + ")";
      }
  }

  customTags();
  setPlatform();

  MathJax.typeset();

  // Process any anchors again now that the proper elements are visible.
  var hash = document.getElementById(location.hash.substr(1));
  if (hash) {
    hash.scrollIntoView();
  }
  
}