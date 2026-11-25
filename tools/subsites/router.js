// CloudFront Function (viewer-request) for the shared intro-page distribution.
// One bucket holds every game's page under a folder named after its subdomain:
//   tilematch.humblelogicgames.com/            -> s3://hlg-sites-.../tilematch/index.html
//   tilematch.humblelogicgames.com/assets/x.js -> s3://hlg-sites-.../tilematch/assets/x.js
// Unknown hosts get 404 so nothing outside the list is served.
var HOSTS = {
  tilematch: 1, onet: 1, bubblepop: 1, nutsxbolts: 1,
  wordsolitaire: 1, amazeout: 1, decodit: 1
};

function handler(event) {
  var req = event.request;
  var host = (req.headers.host && req.headers.host.value) || '';
  var sub = host.split('.')[0].toLowerCase();
  if (!HOSTS[sub]) {
    return { statusCode: 404, statusDescription: 'Not Found' };
  }
  var uri = req.uri;
  if (uri.endsWith('/')) {
    uri += 'index.html';
  } else if (uri.lastIndexOf('.') < uri.lastIndexOf('/')) {
    // "/about" style path without an extension: send to the folder's page
    return {
      statusCode: 301, statusDescription: 'Moved Permanently',
      headers: { location: { value: uri + '/' } }
    };
  }
  req.uri = '/' + sub + uri;
  return req;
}
