// Thin wrapper over the webOS service bridge. Outside a TV it reports that instead of failing.
var TV = (function () {
  var bridges = [];

  function available() { return typeof window.PalmServiceBridge !== 'undefined'; }

  function call(uri, params, done) {
    if (!available()) { done({ returnValue: false, errorText: 'not on a TV' }); return; }
    var b = new window.PalmServiceBridge();
    bridges.push(b); // a bridge that gets garbage collected never calls back
    b.onservicecallback = function (msg) {
      bridges.splice(bridges.indexOf(b), 1);
      var res;
      try { res = JSON.parse(msg); } catch (e) { res = { returnValue: false, errorText: 'bad reply' }; }
      done(res);
    };
    b.call(uri, JSON.stringify(params || {}));
  }

  function launch(id, params, done) {
    // Only send params when a tile has them: an empty object can read as a deep link and give a 404.
    var msg = { id: id };
    if (params) msg.params = params;
    call('luna://com.webos.applicationManager/launch', msg, done);
  }

  function turnOff(done) {
    call('luna://com.webos.service.tvpower/power/turnOff', { reason: 'remoteKey' }, done);
  }

  // Launch data from the PC, when the app was opened with some.
  function launchParams() {
    try { return JSON.parse(window.PalmSystem.launchParams) || {}; } catch (e) { return {}; }
  }

  function exit() { window.close(); }

  return { available: available, launch: launch, turnOff: turnOff, launchParams: launchParams, exit: exit };
})();
