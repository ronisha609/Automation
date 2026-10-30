// D-pad focus. Elements with class "f" are focusable; Left/Right/Up/Down jump to the
// nearest one in that direction by on-screen position, so layouts need no wiring.
var Nav = (function () {
  var KEYS = { 37: 'left', 38: 'up', 39: 'right', 40: 'down', 13: 'ok', 461: 'back', 27: 'back', 8: 'back' };
  var current = null;
  var handlers = {};
  var root = null; // when set, focus stays inside this element (the ringing alarm)

  function candidates() {
    return [].slice.call((root || document).querySelectorAll('.f')).filter(function (el) {
      return el.offsetParent !== null;
    });
  }

  function keepInView(el) {
    var box = el.closest('.scroll');
    if (!box) return;
    var b = box.getBoundingClientRect(), r = el.getBoundingClientRect();
    var pad = 60;
    if (r.bottom + pad > b.bottom) box.scrollTop += r.bottom + pad - b.bottom;
    else if (r.top - pad < b.top) box.scrollTop -= b.top - (r.top - pad);
  }

  function focus(el) {
    if (!el) return;
    if (current) current.classList.remove('focused');
    current = el;
    el.classList.add('focused');
    keepInView(el);
    if (el.onfocused) el.onfocused();
  }

  function distance(dir, a, b) {
    var ax = a.left + a.width / 2, ay = a.top + a.height / 2;
    var bx = b.left + b.width / 2, by = b.top + b.height / 2;
    var main, side;
    if (dir === 'left') { main = a.left - b.right; side = Math.abs(ay - by); }
    else if (dir === 'right') { main = b.left - a.right; side = Math.abs(ay - by); }
    else if (dir === 'up') { main = a.top - b.bottom; side = Math.abs(ax - bx); }
    else { main = b.top - a.bottom; side = Math.abs(ax - bx); }
    if (main < -2) return Infinity; // not in that direction
    // Left/Right stays on the same row, or it would jump diagonally out of the tab bar.
    if ((dir === 'left' || dir === 'right') && (b.bottom <= a.top + 2 || b.top >= a.bottom - 2)) return Infinity;
    return main + side * 2.5;
  }

  function move(dir) {
    if (!current || current.offsetParent === null) { focus(candidates()[0]); return; }
    var from = current.getBoundingClientRect(), best = null, bestD = Infinity;
    candidates().forEach(function (el) {
      if (el === current) return;
      var d = distance(dir, from, el.getBoundingClientRect());
      if (d < bestD) { bestD = d; best = el; }
    });
    if (best) focus(best);
  }

  function onKey(e) {
    var name = KEYS[e.keyCode];
    if (handlers.activity()) { e.preventDefault(); return; } // woke the screensaver
    if (handlers.anyKey()) { e.preventDefault(); return; }
    if (!name) return;
    var typing =document.activeElement && document.activeElement.tagName === 'INPUT';
    if (typing) {
      // The TV's on-screen keyboard owns all keys except finishing or cancelling.
      if (name === 'ok') { e.preventDefault(); handlers.inputDone(document.activeElement); }
      else if (e.keyCode === 461 || e.keyCode === 27) { e.preventDefault(); document.activeElement.blur(); }
      return;
    }
    e.preventDefault();
    if (name === 'back') { if (!root) handlers.back(); }
    else if (name === 'ok') { if (current && current.onok) current.onok(); }
    else move(name);
  }

  function init(h) {
    handlers = h;
    document.addEventListener('keydown', onKey);
  }

  return {
    init: init,
    focus: focus,
    scope: function (el) { root = el; },
    current: function () { return current; }
  };
})();
