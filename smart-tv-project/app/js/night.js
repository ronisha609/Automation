// Night screen: amber or gray clock on black, slow drift, sleep timer, bedtime mode and schedule.
var Night = (function () {
  var DRIFT_MS = 60000;
  var DRIFT_X = 36;
  var DRIFT_Y = 24;
  var el = UI.el;
  var show = function () {};
  var sleepAt = null;
  var sleepTimer = null;
  var wasInWindow = null;

  function st() { return Store.get(); }

  function drift() {
    var wrap = document.getElementById('night-wrap');
    var x = Math.round((Math.random() * 2 - 1) * DRIFT_X);
    var y = Math.round((Math.random() * 2 - 1) * DRIFT_Y);
    wrap.style.transform = 'translate(' + x + 'px,' + y + 'px)';
  }

  function draw() {
    var root = document.querySelector('.night');
    root.classList.toggle('night-gray', st().nightColor === 'gray');
    document.getElementById('night-next').textContent = Alarms.nextText();
    var left = sleepAt ? Math.max(1, Math.ceil((sleepAt - Date.now()) / 60000)) : 0;
    document.getElementById('night-timer').textContent = sleepAt ? 'TV sleeps in ' + left + ' min' : '';
    var btn = document.querySelector('[data-key="sleep"] .val');
    btn.textContent = sleepAt ? left + ' min left' : 'Off';
  }

  function blackout(on) {
    document.getElementById('blackout').classList.toggle('show', on);
  }

  function goToSleep() {
    sleepAt = null;
    draw();
    // A Dev Mode app may not be allowed to power the TV off, so black out the screen instead.
    TV.turnOff(function (res) {
      if (res.returnValue === false) blackout(true);
    });
  }

  function setTimer(mins) {
    clearTimeout(sleepTimer);
    sleepAt = mins ? Date.now() + mins * 60000 : null;
    if (mins) sleepTimer = setTimeout(goToSleep, mins * 60000);
    draw();
  }

  function cycleTimer() {
    var opts = [0, 1, 15, 30, 60, 90];
    var left = sleepAt ? Math.ceil((sleepAt - Date.now()) / 60000) : 0;
    var nextOpt = opts.filter(function (o) { return o > left; })[0] || 0;
    setTimer(nextOpt);
  }

  function bedtime() {
    show('night');
    setTimer(st().sleepMin);
    document.body.classList.add('bedtime');
  }

  // Any remote press leaves bedtime or the blackout. Returns true when the key was used up.
  function wake() {
    var box = document.getElementById('blackout');
    var used = document.body.classList.contains('bedtime') || box.classList.contains('show');
    document.body.classList.remove('bedtime');
    blackout(false);
    return used;
  }

  function inWindow() {
    var d = new Date(), now = d.getHours() * 60 + d.getMinutes();
    var a = st().schedStart, b = st().schedEnd;
    return a <= b ? now >= a && now < b : now >= a || now < b;
  }

  function minute() {
    draw();
    if (!st().schedOn) { wasInWindow = null; return; }
    var inside = inWindow();
    if (inside !== wasInWindow) {
      if (inside) show('night');
      else if (wasInWindow !== null) { wake(); show('home'); }
    }
    wasInWindow = inside;
  }

  function build(root) {
    root.classList.add('night');
    var wrap = el('div');
    wrap.id = 'night-wrap';
    ['night-time', 'night-date', 'night-next', 'night-timer'].forEach(function (id) {
      var d = el('div');
      d.id = id;
      wrap.appendChild(d);
    });
    root.appendChild(wrap);
    var acts = el('div');
    acts.id = 'night-actions';
    UI.row(acts, 'bedtime', 'Bedtime', undefined, bedtime);
    UI.row(acts, 'sleep', 'Sleep timer', 'Off', cycleTimer);
    root.appendChild(acts);
    var box = el('div');
    box.id = 'blackout';
    document.getElementById('app').appendChild(box);
  }

  function init(opts) {
    show = opts.show;
    setInterval(drift, DRIFT_MS);
    draw();
  }

  return { build: build, init: init, draw: draw, minute: minute, wake: wake };
})();
