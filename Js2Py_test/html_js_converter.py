"""
HTML JavaScript Converter

This script uses Js2Py to extract and execute JavaScript embedded in HTML files,
generating static HTML output with the JavaScript effects applied.

Usage:
    python html_js_converter.py input.html output.html

Requirements:
    - Js2Py
    - BeautifulSoup4
    - requests (for fetching HTML from URLs)

Install dependencies:
    pip install js2py beautifulsoup4 requests
"""

import sys
import os
import re
import js2py
from bs4 import BeautifulSoup
import requests


def extract_scripts(html_content):
    """
    Extract JavaScript code from script tags in HTML content.
    
    Args:
        html_content (str): HTML content as string
        
    Returns:
        list: List of JavaScript code blocks
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = []
    
    # Extract inline scripts
    for script_tag in soup.find_all('script'):
        # Skip scripts with src attribute (external scripts)
        if script_tag.get('src'):
            continue
            
        # Skip non-JavaScript scripts
        script_type = script_tag.get('type', 'text/javascript')
        if 'javascript' not in script_type.lower() and script_type != '':
            continue
            
        if script_tag.string:
            scripts.append(script_tag.string)
    
    return scripts


def execute_javascript(js_code):
    """
    Execute JavaScript code using Js2Py.
    
    Args:
        js_code (str): JavaScript code to execute
        
    Returns:
        dict: Context with variables defined by the JavaScript code
    """
    context = js2py.EvalJs()
    try:
        context.execute(js_code)
    except Exception as e:
        print(f"Error executing JavaScript: {e}")
    
    return context


def apply_js_effects(html_content, js_context):
    """
    Apply JavaScript effects to HTML content.
    
    Args:
        html_content (str): Original HTML content
        js_context (dict): JavaScript execution context with variables
        
    Returns:
        str: HTML content with JavaScript effects applied
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find elements with data-js-content attributes
    for elem in soup.find_all(lambda tag: tag.has_attr('data-js-content')):
        var_name = elem.get('data-js-content')
        if hasattr(js_context, var_name):
            # Get the value from JavaScript context
            value = getattr(js_context, var_name)
            
            # Check if the value contains HTML
            if isinstance(value, str) and ('<' in value and '>' in value):
                # Parse the HTML content
                new_content = BeautifulSoup(value, 'html.parser')
                # Replace the element's content with the parsed HTML
                elem.clear()
                elem.append(new_content)
            else:
                # For non-HTML content, just set as string
                elem.string = str(value)
    
    # Find elements with data-js-attr attributes (handle multiple attributes per element)
    for elem in soup.find_all(lambda tag: any(attr.startswith('data-js-attr') for attr in tag.attrs)):
        # Get all data-js-attr attributes
        attr_entries = [attr for attr in elem.attrs if attr.startswith('data-js-attr')]
        
        for attr_entry in attr_entries:
            attr_data = elem.get(attr_entry)
            if ':' in attr_data:
                attr_name, var_name = attr_data.split(':', 1)
                if hasattr(js_context, var_name):
                    # Set the attribute value
                    elem[attr_name] = str(getattr(js_context, var_name))
            
            # Remove the data-js-attr attribute after processing
            del elem[attr_entry]
    
    # Remove script tags
    for script in soup.find_all('script'):
        script.decompose()
    
    return str(soup)


def process_html_file(input_path, output_path):
    """
    Process an HTML file to convert JavaScript to static HTML.
    
    Args:
        input_path (str): Path to input HTML file or URL
        output_path (str): Path to output HTML file
    """
    # Check if input is a URL
    if input_path.startswith(('http://', 'https://')):
        try:
            response = requests.get(input_path)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return
    else:
        # Read HTML file
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    
    # Extract JavaScript
    js_scripts = extract_scripts(html_content)
    
    # Combine all scripts
    combined_js = "\n".join(js_scripts)
    
    # Execute JavaScript
    js_context = execute_javascript(combined_js)
    
    # Apply JavaScript effects to HTML
    static_html = apply_js_effects(html_content, js_context)
    
    # Write output HTML file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(static_html)
        print(f"Static HTML generated successfully: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")


def create_sample_html():
    """
    Create a sample HTML file with embedded JavaScript for testing.
    
    Returns:
        str: Path to the created sample file
    """
    sample_html = """HTTP/2 200 OK
Content-Type: text/html;charset=UTF-8
Vary: Accept-Encoding
P3p: CP="CAO PSA OUR"
X-Application-Context: ace-gateway-s:7001
Server: Tengine/Aserver
Eagleeye-Traceid: 2101590d17531618872418105e0816
Strict-Transport-Security: max-age=31536000
Timing-Allow-Origin: *
Content-Length: 20163
Date: Tue, 22 Jul 2025 05:24:47 GMT
Set-Cookie: xman_us_f=x_locale=ja_JP&x_l=1&x_c_chg=1&acs_rt=cf76e79c38e243cbb293674a11c64cfb; Domain=.aliexpress.com; Expires=Sun, 09-Aug-2093 08:38:54 GMT; Path=/; Secure; SameSite=None
Set-Cookie: intl_locale=ja_JP; Domain=.aliexpress.com; Path=/
Set-Cookie: aep_usuc_f=site=jpn&c_tp=JPY&region=JP&b_locale=ja_JP; Domain=.aliexpress.com; Expires=Sun, 09-Aug-2093 08:38:54 GMT; Path=/; Secure; SameSite=None
Set-Cookie: intl_common_forever=MgWrI3Pi0wT4xYWgjoRAP2vBYytT0IuEHZzzhgYQZo1i1MWSxx/wrw==; Domain=.aliexpress.com; Expires=Sun, 09-Aug-2093 08:38:54 GMT; Path=/; HttpOnly
Set-Cookie: xman_f=ububgzmDGkXe3Ro3i0hRltgkAwBLpDrO03LBp4NM/iyJlPpwtFzlp7XoYEc23EE1MtQepVJKKKxKLlas4HfZ+9esQesvAx1rRX0aO3/TJonoK4vxtXznzg==; Domain=.aliexpress.com; Expires=Sun, 09-Aug-2093 08:38:54 GMT; Path=/; Secure; SameSite=None; HttpOnly
Set-Cookie: acs_usuc_t=x_csrf=10ecdh1ip6itf&acs_rt=cf76e79c38e243cbb293674a11c64cfb; Domain=.aliexpress.com; Path=/; Secure; SameSite=None
Set-Cookie: xman_t=1J8OFuQ5STeSfXdd9gAd0tTP+W+iDOf9Ski0BPMYS15Y2ORlehaVsEfUVm7eBgcy; Domain=.aliexpress.com; Expires=Mon, 20-Oct-2025 05:24:47 GMT; Path=/; Secure; SameSite=None; HttpOnly


<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no"/><link rel="stylesheet" type="text/css" href="//assets.aliexpress-media.com/g/ae-dida/seo-alphabet/0.0.17/index.css" crossorigin="anonymous"/><script>(function(){window._page_config_={loader:{aplus:!0}}})();</script><script>window._dida_config_ = {"pageVersion":"1d83f91d7b218221cecdf0e9548cad9a","pageName":"seo-alphabet","data":{"channel":"price","pageNo":""}};/*!-->init-data-start--*//*!-->init-data-end--*/</script><script>
  !function(){"use strict";window.gep_queue=window.gep_queue||[];function n(e,n){return window.gep_queue.push({action:e,arguments:n})}try{var e,r=(null===(e=document.querySelector('meta[name="aplus-exinfo"]'))||void 0===e?void 0:e.getAttribute("content"))||"";(null==r?void 0:r.split("&")).forEach(function(e){e=e.split("=");"pid"===e[0]&&(window.goldlog_queue||(window.goldlog_queue=[])).push({action:"goldlog.setMetaInfo",arguments:["aplus-cpvdata",{pid:e[1]}]})})}catch(e){}window.addEventListener("error",function(e){n("handleError",[e])},!0),window.addEventListener("unhandledrejection",function(e){n("unhandledrejection",[e])},!0),window.performance&&window.performance.mark&&window.performance.measure&&(window.performance.mark("mark-startRender"),window.performance.measure("startRender","fetchStart","mark-startRender"))}();
  (function(){if(window.dmtrack_pageid)return;try{var cna="001";if(new RegExp("(?:; )?cna=([^;]*);?").test(document.cookie)){var str=decodeURIComponent(RegExp["$1"]);if(str&&str.replace(/(^s*)|(s*$)/g,"").length>0){cna=str}}var page_id=cna.toLowerCase().replace(/[^a-zd]/g,"").substring(0,16);var randend=[page_id,(new Date).getTime().toString(16)].join("");while(randend.length<42){randend+=parseInt(Math.round(Math.random()*1e10),10).toString(16)}window.dmtrack_pageid=randend.substr(0,42)}catch(e){window.dmtrack_pageid="--"}})();
  !function(){"use strict";var e,o=function(e){var o=Object.create(null);return(e=e.trim().replace(/^(\?|#|&)/,""))?(e.split("&").forEach((function(e){var t=e.replace(/\+/g," ").split("="),i=t.shift(),n=t.length>0?t.join("="):void 0;n=void 0===n?null:decodeURIComponent(n),o[i]=n})),o):o};if(window._dida_config_&&!window._dida_config_._init_data_&&(null===(e=window._page_config_)||void 0===e||!e.prefetch)){var t=window._dida_config_,i=t.pageName,n=t.pageVersion,a=t.headers,r=void 0===a?{}:a,s=t.needLogin,c=void 0!==s&&s,l=t.data,d=void 0===l?{}:l,p=t.passQuery;if(i){var u="/fn/".concat(i,"/index");d.pageVersion=n,c&&(d.needLogin=!0),window._page_config_=window._page_config_||{},window._page_config_.prefetch={url:u,data:d,headers:r,withCredentials:!0,passQuery:p}}}!function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{},t=arguments.length>1?arguments[1]:void 0,i=e.enable,n=void 0===i||i,a=e.url,r=e.data,s=void 0===r?{}:r,c=e.headers,l=void 0===c?{}:c,d=e.withCredentials,p=e.passQuery,u=e._init_data_;if(n&&a){var f=t(),_=f.resolve,w=f.reject;if(u)_(u);else{var g,m=function(){return performance&&performance.now?performance.now():(new Date).getTime()},h=m(),v=new XMLHttpRequest,x=a;if(p){var b=o(location.search);"boolean"==typeof p?Object.assign(s,b):Array.isArray(p)&&Object.keys(b).forEach((function(e){-1!==p.indexOf(e)&&(s[e]=b[e])}))}var y=Object.keys(s).map((function(e){return"".concat(e,"=").concat(encodeURIComponent(s[e]))})).join("&");y&&(x+=-1===x.indexOf("?")?"?":"&",x+=y),v.open("GET",x,!0),v.onreadystatechange=function(){if(4===this.readyState){var e,o,t;if(window.clearTimeout(g),"function"==typeof v.getResponseHeader)try{e=v.getResponseHeader("eagleeye-traceid"),o=v.getResponseHeader("x-req-t"),t=v.getResponseHeader("x-req-id")}catch(e){}var i=o||Math.floor(m()-h),n=!!o;if(200===this.status){var a={};try{a=JSON.parse(this.responseText),Object.assign(a,{costTime:i,fromSW:n,traceId:e}),t&&(a.pageId=t),_(a)}catch(o){w({costTime:i,response:this.response,msg:"JSON.parse error!",traceId:e,fromSW:n})}}else w({costTime:i,response:this.response,msg:this.status,traceId:e,fromSW:n})}},"setRequestHeader"in v&&Object.keys(l).forEach((function(e){v.setRequestHeader(e,l[e])})),d&&(v.withCredentials=!0),v.send(),g=window.setTimeout((function(){window.clearTimeout(g),w({costTime:1e4,response:null,msg:"response timeout 10S"}),v.abort()}),1e4)}}}((window._page_config_||{}).prefetch,(function(){var e=null,o=null,t=[],i=[];return window.__INIT_DATA_CALLBACK__=function(n,a){e?n(e):o?a(o):(t.push(n),i.push(a))},{resolve:function(o){e=o,t.forEach((function(e){return e(o)}))},reject:function(e){o=e,i.forEach((function(o){return o(e)}))}}})),(window._page_config_||{}).needLogin&&-1===document.cookie.indexOf("sign=y")&&(location.href="//login.aliexpress.com?return_url=".concat(encodeURIComponent(location.href)));var f={"":{site:"glo",locale:"en_US"},ru:{site:"rus",locale:"ru_RU"},pt:{site:"bra",locale:"pt_BR"},es:{site:"esp",locale:"es_ES"},fr:{site:"fra",locale:"fr_FR"},id:{site:"idn",locale:"in_ID"},it:{site:"ita",locale:"it_IT"},ja:{site:"jpn",locale:"ja_JP"},ko:{site:"kor",locale:"ko_KR"},de:{site:"deu",locale:"de_DE"},ar:{site:"ara",locale:"ar_MA"},nl:{site:"nld",locale:"nl_NL"},th:{site:"tha",locale:"th_TH"},tr:{site:"tur",locale:"tr_TR"},vi:{site:"vnm",locale:"vi_VN"},he:{site:"isr",locale:"iw_IL"},pl:{site:"pol",locale:"pl_PL"}};function _(e,o){e+="=";for(var t=document.cookie.split(";"),i=0;i<t.length;i++){var n=t[i].trim();if(0==n.indexOf(e)){var a=n.substring(e.length,n.length);if(o){var r=new RegExp("(.*&?"+o+"=)(.*?)(&.*|$)");return a.match(r),RegExp.$2}return a}}return""}function w(e,o,t){var i=_(o);i=new RegExp("(.*&?"+t+"=)(.*?)(&.*|$)").test(i)?RegExp.$1+e+RegExp.$3:(i?i+"&":"")+t+"="+e,document.cookie="".concat(o,"=").concat(i,"; Domain=").concat(location.host.split(".").slice(-2).join("."),"; Expires=Sat, 18-Sep-2088 00:00:00 GMT; Path=/;")}var g=window._page_config_||{},m=g.syncCookie,h=g.syncRuCookie;(void 0===h||h)&&function(){if((/aliexpress.ru$/.test(location.host)||/tmall.ru$/.test(location.host))&&!(window.location.href.length>1900)){var e,o,t,i,n,a=(window._robotList||"amsplus,aolbuild,baidu,bingbot,bingpreview,msnbot,adsbot-google,googlebot,mediapartners-google,teoma,slurp,yandex,yandexbot,baiduspider,yeti,seznambot,sogou,yandexmobilebot,msnbot,msnbot-media,sogou,bytespider").split(","),r=_("xman_us_f");r&&-1!=r.indexOf("acs_rt=")||function(){for(var e=!1,o=0,t=a.length;o<t;o++)window.navigator.userAgent&&-1!==window.navigator.userAgent.toLowerCase().indexOf(a[o])&&(e=!0);return e}()||/_s_t=(\d+)/.test(window.location.href)&&!((new Date).getTime()-parseInt(RegExp.$1)>1e4)||(window.location.href="//login.aliexpress.com/sync_cookie_read.htm?xman_goto=".concat(encodeURIComponent((e=window.location.href,o="_s_t",t=(new Date).getTime(),i=new RegExp("([?&])"+o+"=.*?(&|$)","i"),n=-1!==e.indexOf("?")?"&":"?",e.match(i)?e.replace(i,"$1"+o+"="+t+"$2"):e+n+o+"="+t))))}}(),m&&function(){if(-1==["mbest.aliexpress.com","mbest.aliexpress.ru","best.aliexpress.com","best.aliexpress.ru"].indexOf(window.location.host)){var e=function(){var e,o=window.location.host;switch(o){case"m.aliexpress.com":case"www.aliexpress.com":return f[""];case"m.aliexpress.ru":case"www.aliexpress.ru":return f.ru;default:var t=null===(e=o.match(/^(?:m\.)?(ru|pt|es|fr|id|it|ja|ko|de|ar|nl|th|tr|vi|he|pl)?\.aliexpress\.com/))||void 0===e?void 0:e[1];if(t)return f[t]||f[""]}}();if(e){var o=window.location.host,t=_("aep_usuc_f","site");t=function(e){return-1!==Object.keys(f).map((function(e){return f[e].site})).indexOf(e)}(t)?t:"";var i=_("aep_usuc_f","b_locale");if(!t||"m.aliexpress.com"!==o&&"www.aliexpress.com"!==o&&e.locale!==i)return w(e.site,"aep_usuc_f","site"),void w(e.locale,"aep_usuc_f","b_locale");if("glo"!==t){var n=function(e){for(var o="",t=Object.keys(f),i=0;i<t.length;i++)if(f[t[i]].site===e){o=t[i];break}return o}(t);"m.aliexpress.com"===o?location.href=location.href.replace(/^https:\/\/m\.aliexpress\.com/,"ru"===n?"https://m.aliexpress.ru":"https://m.".concat(n,".aliexpress.com")):"www.aliexpress.com"===o&&(location.href=location.href.replace(/^https:\/\/www\.aliexpress\.com/,"ru"===n?"https://aliexpress.ru":"https://".concat(n,".aliexpress.com")))}}}}()}();
</script>
<script>
!function(){"use strict";!function(){try{if(window.performance&&window.MutationObserver){var e=Date.now(),t=document.body||document.documentElement,r=new MutationObserver((function(t){if(Date.now()-e>1e4)r.disconnect();else if(function(){if(document.querySelector("[data-TTICheck]"))return!0;var e,t;switch(document.querySelector("body")&&(e=document.querySelector("body").getAttribute("data-spm")),e){case"detail":t=document.querySelector("[data-pl=product-title]")||document.querySelector(".title--line-one--nU9Qtto");break;case"cart":case"shopcart":t=document.querySelector("div.cart-body");break;case"home":t=document.querySelector("div.home--new-home--UXKZmgj")||document.querySelector("div#root-child");break;case"productlist":t=document.querySelector("div.manhattan--outWrapper--27DvdWd")||document.querySelector("#card-list");break;case"best":t=document.querySelector("div.new-affiliate")||document.querySelector("div#root-child");break;case"placeorder":case"createOrder":t=document.querySelector(".pl-place-order-container")}return!!t}()){performance.mark("self-tti"),performance.measure("tti","fetchStart","self-tti");var o=performance.getEntriesByName("tti")[0];window.GepTrackerPerfQueue=window.GepTrackerPerfQueue||[],window.GepTrackerPerfQueue.push(["TTI",Math.round(o.duration)]),r.disconnect()}}));r.observe(t,{childList:!0,subtree:!0})}}catch(e){console.error(e)}}()}();
</script>
<meta name="aplus-plugin-aefront-ignore-force-set-meta" content="true" />
<script>
!function(){"use strict";var s,o;s=window.goldlog_queue||(window.goldlog_queue=[]),o="aplus.aliexpress.com",/aliexpress.us$/.test(window.location.host)&&(o="aplus.aliexpress.us"),s.push({action:"goldlog.setMetaInfo",arguments:["aplus-rhost-v",o+"/g.gif"]}),s.push({action:"goldlog.setMetaInfo",arguments:["aplus-rhost-g",o]})}();
</script></head><body><script type="text/javascript">
(function(){try{var e=document.querySelector("body"),t=e.getAttribute("data-spm");if("detail"!==t||!window.localStorage||document.getElementById("__top_banner_img__"))return;var r=window.localStorage.getItem("_sync_detail_banner_")||"";if(!r)return;var n=r.split("||");if(n&&3===n.length){var a=n[0],i=n[1],o=parseInt(n[2]);if((new Date).getTime()-o>36e5)return;var d=document.createElement("div");d.setAttribute("id","__top_banner_img__"),d.setAttribute("data-spm","100003"),d.setAttribute("class","top-banner-container");var c=document.createElement("a");c.setAttribute("href",a),c.style.backgroundImage="url("+i+")",c.innerHTML="&nbsp;",d.appendChild(c);var l=document.querySelector("body");l&&l.insertBefore(d,l.firstChild)}}catch(e){}})();
</script>










<link rel="stylesheet" type="text/css" href="https://assets.alicdn.com/g/ae-fe/header-ui/0.0.46/src/multilan/ae-header-ltr.css">





<div class="top-lighthouse" data-spm="1000001" id="top-lighthouse">
    <div class="top-lighthouse-wrap container">
        <div class="ae-logo default-hidden-logo"><a class="logo-link" href="//www.aliexpress.com"><span class="logo-info">AliExpress</span></a></div>
        <div class="nav-global" id="nav-global">
            
            
            <div class="ng-item-wrap ng-help-wrap">
                <div class="ng-item ng-help ng-sub">
                    <span class="ng-sub-title">ヘルプセンター</span>
                    <ul class="ng-sub-list">
                        
                        
                        <li><a data-role="help-center-link" class="ng-help-link" href="//service.aliexpress.com/page/home?pageId=17&language=en" rel="follow">顧客サービス</a></li>
                        
                        
                        
                        
                        
                        
                        
                        
                        <li><a data-role="complaint-link" href="//report.aliexpress.com" rel="nofollow">紛争</a></li>
                        <li><a data-role="ipp-link" href="//ipp.alibabagroup.com/index.htm" rel="nofollow">知的財産権の侵害を報告</a></li>
                    </ul>
                </div>
                <div class="ng-item ng-bp"><a href="//sale.aliexpress.com/v8Yr8f629D.htm" rel="nofollow">消費者保護</a></div>
                <div class="ng-item ng-mobile"><a href="//sale.aliexpress.com/download_app_guide.htm" rel="nofollow">モバイル</a></div>
            </div>
            <div class="ng-item-wrap ng-item ng-switcher" data-role="region-pannel">
                <!-- switcher start -->
                <div data-role="region-pannel">
                    <a id="switcher-info" data-role="menu" class="switcher-info notranslate" rel="nofollow" href="javascript:void(0)">&nbsp;</a>
                    <div class="switcher-sub notranslate" data-role="content">
                        <div class="switcher-common">
                            <div class="switcher-shipto item util-clearfix">
                                <span class="label">送り先</span>
                                <div data-role="switch-country" class="country-selector switcher-shipto-c"></div>
                            </div>
                            <div class="switcher-language item util-clearfix">
                                <span class="label">言語</span>
                            </div>
                            <div class="switcher-currency item util-clearfix">
                                <span class="label">貨幣</span>
                                <div class="switcher-currency-c" data-role="switch-currency"></div>
                            </div>
                
                            <div class="switcher-btn item util-clearfix">
                                <button type="button" data-role="save" class="ui-button ui-button-primary go-contiune-btn">預金</button>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- switcher end -->
            </div>
            <div class="ng-item-wrap ng-personal-info">
                <div class="ng-item nav-pinfo-item nav-cart nav-cart-box">
                    <a class href="//shoppingcart.aliexpress.com/shopcart/shopcartDetail.htm" rel="nofollow">
                        <i class="ng-cart-icon ng-icon-size"></i><span class="text">カーと</span>
                        <span class="cart-number" id="nav-cart-num" ami-survive="1"></span>
                    </a>
                </div>
                <div class="ng-item nav-pinfo-item nav-wishlist">
                    <a href="//my.aliexpress.com/wishlist/wish_list_product_list.htm" rel="nofollow">
                        <i class="ng-wishlist-icon ng-icon-size"></i><span class="text">願望リスト</span>
                    </a>
                </div>
                <div class="ng-item nav-pinfo-item nav-user-account" id="nav-user-account">
                    <span class="user-account-port">
                        <a data-role="myaliexpress-link" href="javascript:;">
                            <i class="ng-account-icon ng-icon-size" ami-survive="1"></i><span class="text">アカウント</span>
                        </a>
                    </span>
                    <div class="user-account-main" data-role="user-account-main">
                        <div class="flyout-user-signIn flyout-new-user" data-role="user-signIn" style="display: block;">
                            <p class="flyout-welcome-wrap">AliExpress.comへようこそ</p>
                            <div class="flyout-logined">
                                <i class="flyout-user-avatar"><img data-role="avatar-img" src alt></i>
                                <p class="flyout-welcome-text" data-role="flyout-welcome">Welcome back</p>
                            </div>
                            <p class="flyout-sign-out" data-role="signout-btn"><a href="//login.aliexpress.com/xman/xlogout.htm" rel="nofollow">サインアウト</a></p>
                            <p class="flyout-bottons">
                                <a class="join-btn" data-role="join-link" href="javaScript:;" rel="nofollow">加入</a>
                                <a class="sign-btn" data-role="sign-link" href="javaScript:;" rel="nofollow">サインイン</a>
                            </p>
                        </div>
                        <i class="flyout-line">&nbsp;</i>
                        <ul class="flyout-quick-entry" data-role="quick-entry">
                            <li><a href="//www.aliexpress.com/p/order/index.html" rel="nofollow">私の注文</a></li>
                            <li><a href="//msg.aliexpress.com?tracelog=ws_topbar" rel="nofollow">メッセージセンター<span class="unread-message-count" ami-survive="1"></span></a></li>
                            <li><a href="//my.aliexpress.com/wishlist/wish_list_product_list.htm" rel="nofollow">願望リスト</a></li>
                            <li><a href="//my.aliexpress.com/wishlist/wish_list_store_list.htm" rel="nofollow" class="js-menu-my-favorite-stores">私の好きな店</a></li>
                            <li><a href="//coupon.aliexpress.com/buyer/coupon/listView.htm" rel="nofollow">私のクーポン</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>


<style type="text/css">
.default-hidden-logo{display:none;}
.header.header-fixed-status{z-index:990;}
.header-tag-search .hm-right .right-shopcart{z-index: 11;}
.header-tag-home .site-logo a{width: 240px;height: 76px;}
.top-lighthouse .nav-user-account .flyout-welcome-text{overflow:hidden;}
@media (max-width:1230px) {.festival-logo>a>span>img{width: auto !important;}}
</style>
<script type="text/javascript">
    (function(){
        window.globalSiteNormalSidebarConfig = {
            isShowSidebar: true,
            isShowSellerCoupon: true,
            newUserUrl: 'https://campaign.aliexpress.com/wow/gcp/new-user-channel/index?wh_weex=true&wx_navbar_hidden=true&wx_navbar_transparent=true&ignoreNavigationBar=true&wx_statusbar_hidden=true&_immersiveMode=true&preDownLoad=true&tabType=gift',
        }
        
        var appendFunc = function () {
            if (document.getElementById('__global__header__')) {
                return;
            }

            var url = "https://assets.alicdn.com/g/ae-fe/header-ui/0.0.46/src/ae-header.js";
            var b = document.createElement("script");
            b.setAttribute("defer", "defer");
            b.setAttribute("type", "text/javascript");
            b.setAttribute("src", url);
            b.setAttribute("crossorigin", "anonymous");
            b.setAttribute('id', '__global__header__');
            document.getElementsByTagName('head') && document.getElementsByTagName('head')[0].appendChild(b);
        };
        setTimeout(function(){
            appendFunc()
        },5000);
        
        window.__global_header_init__ = appendFunc;
    })();
</script><!-- 预发布引入示意 -->

<script src="https://assets.aliexpress-media.com/g/code/npm/@alife/nano-cross-page-loader/0.0.35/_cross_page_loader_.js" crossorigin></script>



<div id="root"></div><!-- cosmos start -->

<script>
    window._is_close_global_abtest = true;
    window._ae_pic_a1_on_ = true;
    window._disable_header_gdpr_ = true;
</script>
<link rel="stylesheet" href="https://assets.aliexpress-media.com/g/ae-fe/cosmos/0.0.387/pc/index.css">
<script src="https://assets.aliexpress-media.com/g/ae-fe/global/0.0.3/index.js" crossorigin></script>
<script src="https://assets.aliexpress-media.com/g/ae-fe/cosmos/0.0.387/pc/index.js" crossorigin></script>
<script src="https://assets.alicdn.com/g/lzd_sec/LWSC-G/index.js" crossorigin></script>
<!-- cosmos end --><script src="//assets.aliexpress-media.com/g/ae-dida/seo-alphabet/0.0.17/index.js" crossorigin="anonymous"></script></body></html>"""
    
    sample_path = os.path.join(os.path.dirname(__file__), "sample.html")
    with open(sample_path, 'w', encoding='utf-8') as f:
        f.write(sample_html)
    
    return sample_path


def main():
    """
    Main function to handle command line arguments and process HTML files.
    """
    # If no arguments provided, create and process a sample file
    if len(sys.argv) < 3:
        print("No input/output files specified. Creating and processing a sample file...")
        sample_path = create_sample_html()
        output_path = os.path.join(os.path.dirname(__file__), "sample_static.html")
        process_html_file(sample_path, output_path)
    else:
        # Process the specified input and output files
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        process_html_file(input_path, output_path)


if __name__ == "__main__":
    main()