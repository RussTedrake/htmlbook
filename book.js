
// Definitions for mathjax
var mathjax_setup = `
<div style="display:none" id="mathjax_setup"> 
  \\[
  \\newcommand{\\pd}[2]{\\frac{\\partial #1}{\\partial #2}}
  \\newcommand{\\Re}{{\\mathbb{R}}}
  \\newcommand{\\bc}{{\\bf c}}
  \\newcommand{\\bg}{{\\bf g}}
  \\newcommand{\\bh}{{\\bf h}}
  \\newcommand{\\bp}{{\\bf p}}
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
  \\newcommand{\\bD}{{\\bf D}}
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
  \\newcommand{\\find}{\\operatorname{\\textrm{find}}}
  \\newcommand{\\minimize}{\\operatorname{\\textrm{minimize}}}
  \\newcommand{\\maximize}{\\operatorname{\\textrm{maximize}}}
  \\DeclareMathOperator*{\\find}{find}
  \\DeclareMathOperator*{\\rank}{rank}
  \\DeclareMathOperator{\\tr}{tr}
  \\newcommand{\\argmax}{\\operatorname{\\textrm{argmax}}}
  \\newcommand{\\argmin}{\\operatorname{\\textrm{argmin}}}
  \\newcommand{\\atantwo}{\\operatorname{\\textrm{atan2}}}
  \\newcommand{\\sgn}{\\operatorname{\\textrm{sgn}}}
  \\newcommand{\\trace}{\\operatorname{\\textrm{tr}}}
  \\newcommand{\\sos}{\\text{ is SOS}}
  \\]
</div>

<div id="debug_output"></div>
`;

function setPlatform(platform) {
  function hide(items) { for (let item of items) { item.style.display = "none"; } }
  function show(items) { for (let item of items) { item.style.display = "inline"; } }

  hide(document.getElementsByClassName("mac"));
  hide(document.getElementsByClassName("bionic"));
  hide(document.getElementsByClassName("focal"));

  show(document.getElementsByClassName(platform));
}

function customTags() {
  // We cannot add a link via CSS, so do it here instead.
  var drakeTags = document.getElementsByTagName('drake');
  for (j = 0; j < drakeTags.length; j++) {
      drakeTags[j].innerHTML =
      '<a style="font-variant:small-caps; text-decoration:none;" href="http://drake.mit.edu">Drake</a>';
  }

  var bib = [];

  var elibTags = document.getElementsByTagName('elib');
  for (i = 0; i < elibTags.length; i++) {
    var c = elibTags[i].innerHTML;
    var str = "";
    var index;
    c.split("+").forEach(function(b) {
      b = b.trim();
      index = bib.indexOf(b);
      if (index == -1) {
        index = bib.length;
        bib.push(b);
      }
      if (str.length > 0) {
        str += ", ";
      }
      str += '<a href="#' + b + '">' + (index+1) + '</a>';
    });
    // for citing part of a work: https://blog.apastyle.org/apastyle/2013/11/how-to-cite-part-of-a-work.html
    if (elibTags[i].hasAttribute('part')) {
      str += ", " + elibTags[i].getAttribute('part');
    }
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

function loadIndex()  {
  forwardOldChapterLink();
  customTags();
  var mathjax = document.getElementById("mathjax");
  mathjax.innerHTML = mathjax_setup + mathjax.innerHTML;
  MathJax.typeset();
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
      var file = codeTags[j].innerHTML;
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = ( function (j) { return function() {
          if (this.readyState == 4 && this.status == 200) {
              var text = hljs.highlight('python',this.responseText,true)
              codeTags[j].innerHTML =
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
      '<p><pre style="margin-left:6px; display:inline"><code>python3 <a target="' + file +'" href="' + file + '">' + file + '</a>';
      if (pysrcTags[j].hasAttribute("args")) {
          tmp += ' '+ pysrcTags[j].getAttribute("args");
      }
      tmp += '</code></pre>';
      if (!pysrcTags[j].hasAttribute("no_colab")) {
        tmp +=
        '<sidenote><a style="font-size:8pt; margin-left:50%" target="scratchpad" href="https://colab.research.google.com/github/RussTedrake/underactuated/blob/master/setup/colab_scratchpad.ipynb">' + 'Colab scratchpad</a></sidenote>';
      }
      pysrcTags[j].innerHTML = tmp + '</p>';
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
  platform = 'focal';
  if (navigator.appVersion.indexOf("Mac")>=0) { platform = 'mac'; }
  setPlatform(platform);

  MathJax.typeset();

  // Process any anchors again now that the proper elements are visible.
  var hash = document.getElementById(location.hash.substr(1));
  if (hash) {
    hash.scrollIntoView();
  }
  
}

function system_html(sys, url = null) {
  let input_port_html = "";
  if ('input_ports' in sys) {
    sys.input_ports.forEach(port => {
      input_port_html += `<tr><td align=right style=\"padding:5px 0px 5px 0px\">${port}&rarr;</td></tr>`;
    });
  }
  let output_port_html = "";
  if ('output_ports' in sys) {
    sys.output_ports.forEach(port => {
      output_port_html += `<tr><td align=left style=\"padding:5px 0px 5px 0px\">&rarr; ${port}</td></tr>`;
    });
  }
  let name_html = sys.name;
  if (url) {
    name_html = `<a href="${url}">${sys.name}</a>`;
  }
  return `<table align=center cellpadding=0 cellspacing=0><tr align=center><td style=\"vertical-align:middle\"><table cellspacing=0 cellpadding=0>${input_port_html}</table></td><td align=center style=\"border:solid;padding-left:20px;padding-right:20px;vertical-align:middle\" bgcolor=#F0F0F0>${name_html}</td><td style=\"vertical-align:middle\"><table cellspacing=0 cellpadding=0>${output_port_html}</table></td></tr></table>`;
}

function notebook_header(chapter) {
  if (chapter in chapter_project_ids) {
    return `<a href="https://deepnote.com/workspace/${deepnote_workspace_id}/project/${chapter_project_ids[chapter]}/" style="float:right; margin-top:20px; margin-bottom:-100px;background:white;border:0;" target="${chapter}">
    <img src="https://deepnote.com/buttons/launch-in-deepnote-white.svg"></a>
    <div style="clear:right;"></div>`;
  }
  return "";
}

drake_tutorials_id = "2b4fc509-aef2-417d-a40d-6071dfed9199"
drake_workspace_id = "Drake-0b3b2c53-a7ad-441b-80f8-bf8350752305"

function drake_tutorials_link(name, link_text="") {
  // TODO(russt): Retrieve IDs for sp
  if (link_text) {
    return `<a href="https://deepnote.com/workspace/${drake_workspace_id}/project/${drake_tutorials_id}" target="drake_tutorials">${link_text}</a>`;
  } else {
    return `<p><a href="https://deepnote.com/workspace/${drake_workspace_id}/project/${drake_tutorials_id}" style="background:none; border:none;" target="drake_tutorials">  <img src="https://deepnote.com/buttons/launch-in-deepnote-white.svg"></a></p>`;
  }
}

function notebook_link(chapter, notebook, link_text="") {
  if (!notebook) { notebook = chapter; }
  chapter_project_id = chapter_project_ids[chapter];
  notebook_id = notebook_ids[chapter][notebook];
  if (notebook_id) {
    if (link_text) {
      return `<a href="https://deepnote.com/workspace/${deepnote_workspace_id}/project/${chapter_project_id}/notebook/${notebook}-${notebook_id}" target="${chapter}">${link_text}</a>`;
    } else {
      return `<p><a href="https://deepnote.com/workspace/${deepnote_workspace_id}/project/${chapter_project_id}/notebook/${notebook}-${notebook_id}" style="background:none; border:none;" target="${chapter}">  <img src="https://deepnote.com/buttons/launch-in-deepnote-white.svg"></a></p>`;
    }
  }
  return `<p><center>ERROR: <i>Notebook link not found. Please do a "force reload" of this page. If that doesn't fix it, please email russt@mit.edu and let me know.</i></center></p>`;
}

function copy_code_to_clipboard(buttonElement) {
  const codeElement = buttonElement.parentElement.nextElementSibling.querySelector('code');
  const text = codeElement.textContent;

  const textArea = document.createElement('textarea');
  textArea.textContent = text;
  document.body.appendChild(textArea);
  textArea.select();

  document.execCommand('copy');
  document.body.removeChild(textArea);
}