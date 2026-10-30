// Small helpers shared by the screens.
var UI = (function () {
  var toastTimer = null;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function toast(msg) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('show'); }, 2600);
  }

  function clock(h, m) {
    if (Store.get().clock24) return pad(h) + ':' + pad(m);
    return (h % 12 || 12) + ':' + pad(m) + (h < 12 ? ' AM' : ' PM');
  }

  // Minutes after midnight as display text.
  function minutes(total) { return clock(Math.floor(total / 60), total % 60); }

  // A settings-style row. Focus survives redraws through its data-key.
  function row(parent, key, label, value, onok) {
    var r = el('div', 'row f');
    r.setAttribute('data-key', key);
    r.appendChild(el('span', '', label));
    if (value !== undefined) r.appendChild(el('span', 'val', value));
    r.onok = onok;
    parent.appendChild(r);
    return r;
  }

  function mini(parent, key, label, onok, on) {
    var b = el('div', 'row mini f' + (on ? ' on' : ''), label);
    b.setAttribute('data-key', key);
    b.onok = onok;
    parent.appendChild(b);
    return b;
  }

  // Rebuilds a list, then puts focus back on the same control if it still exists.
  function redraw(box, build) {
    var cur = Nav.current();
    var key = cur && box.contains(cur) ? cur.getAttribute('data-key') : null;
    var top = box.scrollTop;
    box.textContent = '';
    build();
    box.scrollTop = top;
    if (key) Nav.focus(box.querySelector('[data-key="' + key + '"]') || box.querySelector('.f'));
  }

  return { el: el, pad: pad, toast: toast, clock: clock, minutes: minutes, row: row, mini: mini, redraw: redraw };
})();
