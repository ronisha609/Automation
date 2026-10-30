// Guest Wi-Fi QR. Generated on the TV. Credentials arrive from scripts/push_config.py and stay on the TV.
var Guest = (function () {
  var el = UI.el;
  var QR_PX = 600;
  var QUIET_MODULES = 4;

  function esc(s) { return String(s).replace(/([\\;,:"])/g, '\\$1'); }

  function wifiText(g) {
    if (g.security === 'nopass') return 'WIFI:T:nopass;S:' + esc(g.ssid) + ';;';
    return 'WIFI:T:' + (g.security || 'WPA') + ';S:' + esc(g.ssid) + ';P:' + esc(g.password) + ';;';
  }

  function paint(canvas, text) {
    qrcode.stringToBytes = qrcode.stringToBytesFuncs['UTF-8'];
    var q = qrcode(0, 'M');
    q.addData(text);
    q.make();
    var count = q.getModuleCount(), total = count + QUIET_MODULES * 2;
    var cell = Math.floor(QR_PX / total);
    var size = cell * total;
    canvas.width = canvas.height = size;
    var c = canvas.getContext('2d');
    c.fillStyle = '#fff';
    c.fillRect(0, 0, size, size);
    c.fillStyle = '#000';
    for (var r = 0; r < count; r++) {
      for (var col = 0; col < count; col++) {
        if (q.isDark(r, col)) c.fillRect((col + QUIET_MODULES) * cell, (r + QUIET_MODULES) * cell, cell, cell);
      }
    }
  }

  function draw() {
    var g = Store.get().guest;
    var canvas = document.getElementById('guest-qr');
    canvas.style.display = g ? 'block' : 'none';
    document.getElementById('guest-title').textContent = g ? 'Scan to join Wi-Fi' : 'Guest Wi-Fi is not set up';
    document.getElementById('guest-name').textContent = g ? g.ssid : 'Run scripts/push_config.py on your PC to add it.';
    if (g) paint(canvas, wifiText(g));
  }

  function build(root) {
    root.classList.add('guest');
    var qr = el('canvas');
    qr.id = 'guest-qr';
    root.appendChild(qr);
    var text = el('div');
    text.id = 'guest-text';
    var t = el('h1');
    t.id = 'guest-title';
    var n = el('p');
    n.id = 'guest-name';
    text.appendChild(t);
    text.appendChild(n);
    root.appendChild(text);
  }

  return { build: build, draw: draw };
})();
