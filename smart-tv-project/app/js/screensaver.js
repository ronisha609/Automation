// Ambient screensaver: original slow-drifting scenes that cross-fade, with a clock overlay.
// Pure CSS gradients, so it stays light on this TV's memory. Any remote key wakes it.
var Screensaver = (function () {
  var el = UI.el;
  var SCENES = ['ss-aurora', 'ss-dusk', 'ss-city', 'ss-dawn', 'ss-forest', 'ss-deep'];
  var CYCLE_MS = 18000;
  var lastActivity = Date.now();
  var active = false;
  var idx = 0;
  var front = 0;
  var layers = [];
  var cycleTimer = null;

  function st() { return Store.get(); }

  function build() {
    var box = el('div');
    box.id = 'screensaver';
    layers = [el('div', 'ss-layer'), el('div', 'ss-layer')];
    layers.forEach(function (l) { box.appendChild(l); });
    var c = el('div');
    c.id = 'ss-clock';
    var d = el('div');
    d.id = 'ss-date';
    box.appendChild(c);
    box.appendChild(d);
    document.getElementById('app').appendChild(box);
  }

  function tick() {
    var d = new Date();
    document.getElementById('ss-clock').textContent = UI.clock(d.getHours(), d.getMinutes());
    document.getElementById('ss-date').textContent =
      d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  }

  function advance() {
    idx = (idx + 1) % SCENES.length;
    var back = 1 - front;
    layers[back].className = 'ss-layer ' + SCENES[idx] + ' panning';
    layers[back].style.opacity = '1';
    layers[front].style.opacity = '0';
    front = back;
    tick();
  }

  function show() {
    if (active) return;
    active = true;
    idx = Math.floor(Math.random() * SCENES.length);
    front = 0;
    layers[0].className = 'ss-layer ' + SCENES[idx] + ' panning';
    layers[0].style.opacity = '1';
    layers[1].style.opacity = '0';
    tick();
    document.getElementById('screensaver').classList.add('show');
    cycleTimer = setInterval(advance, CYCLE_MS);
  }

  function hide() {
    if (!active) return;
    active = false;
    clearInterval(cycleTimer);
    document.getElementById('screensaver').classList.remove('show');
  }

  // Called on every remote key. Returns true when it used the key to wake the screensaver.
  function activity() {
    lastActivity = Date.now();
    if (active) { hide(); return true; }
    return false;
  }

  function check() {
    if (!st().saverOn || active) return;
    // Don't cover the bedtime screen or interrupt a ringing alarm.
    if (document.body.classList.contains('bedtime')) return;
    if ((Date.now() - lastActivity) >= st().saverDelay * 60000) show();
  }

  function init() {
    build();
    setInterval(check, 5000);
  }

  return { init: init, activity: activity, isActive: function () { return active; } };
})();
