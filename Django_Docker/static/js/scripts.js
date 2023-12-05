/*!
* Start Bootstrap - Modern Business v5.0.7 (https://startbootstrap.com/template-overviews/modern-business)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-modern-business/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project



// bootstrapでのデフォルトのブレークポイントで発火
const breakPoint = {
    class: {
        "xs" : 0,
        "sm" : 576,
        "md" : 768,
        "lg" : 992,
        "xl" : 1200,
        "xxl": 1400,
    },
    width: null,
    last: null,
    check: function () {
        this.width = window.innerWidth;

        let pt = Object.values(this.class);
        let n = null;
        if      (this.width >= pt[5]) n = 5;
        else if (this.width >= pt[4]) n = 4;
        else if (this.width >= pt[3]) n = 3;
        else if (this.width >= pt[2]) n = 2;
        else if (this.width >= pt[1]) n = 1;
        else n = 0;

        if (n == this.last) return false;
        this.last = n;

        console.log(`\nthis.width: ${this.width} px`);
        console.log("transition_class: " + Object.keys(this.class)[this.last]);
        console.log(`this.last :  ${this.last}`);
        return true;
    }
}

breakPoint.check();
