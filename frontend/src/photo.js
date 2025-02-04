// Photo class written with the help of Bing AI.
// the whole purpose is to automatically generate low-resolution proxies to speed up
// applications where a low-res proxy is good enough.
export class Photo {
    constructor(hiResBlob, lowResBlob) {
        this._originalURL = URL.createObjectURL(hiResBlob);
        this._proxyURL = URL.createObjectURL(lowResBlob);
    }
}
