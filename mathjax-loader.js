// Load exactly one MathJax runtime.  The configuration script must precede this
// script.  Pages wait for mathjaxReady before requesting typesetting.
window.mathjaxReady = (async function () {
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.id = 'MathJax-script';
      script.src = src;
      script.onload = resolve;
      script.onerror = () => {
        script.remove();
        reject(new Error('Unable to load MathJax from ' + src));
      };
      document.head.appendChild(script);
    });
  }

  try {
    await loadScript('https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-chtml.js');
  } catch (error) {
    // The optional local npm installation includes the font data and web fonts.
    // Without this path, even a local runtime fetches its fonts from the CDN.
    MathJax.loader = MathJax.loader || {};
    MathJax.loader.paths = MathJax.loader.paths || {};
    MathJax.loader.paths['mathjax-newcm'] =
      'htmlbook/MathJax/node_modules/@mathjax/mathjax-newcm-font';
    await loadScript('htmlbook/MathJax/node_modules/mathjax/tex-chtml.js');
  }
  await MathJax.startup.promise;
})();
