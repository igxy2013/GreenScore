/*
 * iframe-resizer v4.3.2 - Copyright (c) 2021 David J. Bradshaw - dave@bradshaw.net
 * License: MIT
 */

!function(u){if("undefined"!=typeof window){var e,t,n,a=0,i=!1,o=!1,r="message".length,c="[iFrameSizer]",s=c.length,f=null,l=window.requestAnimationFrame,m={max:1,scroll:1,bodyScroll:1,documentElementScroll:1},d={},h=null,g={autoResize:!0,bodyBackground:null,bodyMargin:null,bodyMarginV1:8,bodyPadding:null,checkOrigin:!0,inPageLinks:!1,enablePublicMethods:!0,heightCalculationMethod:"bodyOffset",id:"iFrameResizer",interval:32,log:!1,maxHeight:1/0,maxWidth:1/0,minHeight:0,minWidth:0,mouseEvents:!0,resizeFrom:"parent",scrolling:!1,sizeHeight:!0,sizeWidth:!1,warningTimeout:5e3,tolerance:0,widthCalculationMethod:"scroll",onClose:function(){return!0},onClosed:function(){},onInit:function(){},onMessage:function(){E("onMessage function not defined")},onMouseEnter:function(){},onMouseLeave:function(){},onResized:function(){},onScroll:function(){return!0}},p={};window.jQuery&&function(e){e.fn?e.fn.iFrameResize||(e.fn.iFrameResize=function(t){return this.filter("iframe").each(function(e,n){q(n,t)}).end()}):I("","Unable to bind to jQuery, it is not fully loaded.")}(window.jQuery),window.iFrameResize=window.iFrameResize||function(){for(var e=["moz","webkit","o","ms"],t=0;t<e.length&&!window.requestAnimationFrame;++t)window.requestAnimationFrame=window[e[t]+"RequestAnimationFrame"],window.cancelAnimationFrame=window[e[t]+"CancelAnimationFrame"]||window[e[t]+"CancelRequestAnimationFrame"];if(!window.requestAnimationFrame){var i=0;window.requestAnimationFrame=function(e){var t=(new Date).getTime(),n=Math.max(0,16-(t-i)),o=window.setTimeout(function(){e(t+n)},n);return i=t+n,o},window.cancelAnimationFrame=function(e){clearTimeout(e)}}},window.addEventListener("message",function(t){var n,o,a,i,r,c,s,f,l=t.data,m=l.indexOf("]")+1,d=l.substring(0,m),h=l.substring(m);d===c+"["+a+"]"&&(s=h.split(":"),f=s[0],i=s[1],r=s[2],o=i,function(){var e=window.location.href,t=document.createElement("a");t.href=o,t.host!==t.hostname&&(t.host!==e.host||t.protocol!==e.protocol||t.port!==e.port)?I("Ignored: "+o):I("Valid: "+o)}()&&(n={iframe:document.getElementById(a),id:a,height:i,width:r,type:f},p[n.id]&&(p[n.id].loaded=!0),(!d||p[n.id]&&p[n.id].firstRun)&&function(e){var t=e.id,n=e.type;e.iframe?p[t]?W(t,n):R(e):E(t+" No document found")}(n)))}),window.iFrameResize=function(e,t){var n,o,a;if("string"==typeof t&&(a=t,t={}),a&&(t=t||{},t.id=a),"object"!=typeof t&&(t={}),t=T({},g,t),p[t.id]&&(p[t.id].loaded=!0),n="string"==typeof e?document.getElementById(e):e,!n)throw new TypeError("Object is not a valid DOM element");return o=function(e,t){var n=T({},g,t);return p[e]={iframe:document.getElementById(e),settings:n,loaded:!1},e}(n.id||function(){var e=t.id||d.id+a++;return null!==document.getElementById(e)&&(e+=a++),e}(),t),o}}}(window),function(){if("function"!=typeof window.CustomEvent){function e(e,t){t=t||{bubbles:!1,cancelable:!1,detail:void 0};var n=document.createEvent("CustomEvent");return n.initCustomEvent(e,t.bubbles,t.cancelable,t.detail),n}e.prototype=window.Event.prototype,window.CustomEvent=e}}();

// 初始化自定义配置
window.iFrameResizer = window.iFrameResizer || {
    heightCalculationMethod: function() {
        // 获取文档完整高度
        return Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.offsetHeight,
            document.body.clientHeight,
            document.documentElement.clientHeight
        );
    },
    autoResize: true,
    onMessage: function(msg) {
        console.log('收到消息:', msg);
    },
    onReady: function() {
        console.log('iframe-resizer 准备就绪');
    }
};

// 调试信息
console.log('iframe-resizer.contentWindow.js 已加载'); 