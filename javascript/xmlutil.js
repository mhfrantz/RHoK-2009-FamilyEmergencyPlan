/*
Copyright 2009 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/**
 * @fileoverview Contains some helper methods for dealing with XML and XML/JSON
 * conversion in the browser. These methods were designed for working with the
 * JS GData client library, but can likely be adopted for other uses.
 * @author api.roman.public@gmail.com (Roman Nurik)
 */

/**
 * Parses a string of XML into a browser XML DOM node.
 * @param {string} xml The XML string to parse.
 * @return {Node} The node, representing either the parsed XML or
 *     <parsererror>'s that occurred.
 */
function parseXml(xml) {
  var xmlDoc;
  try {
    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');
    xmlDoc.async = false;
    xmlDoc.loadXML(xml);
  } catch (e) {
    xmlDoc = (new DOMParser).parseFromString(xml, 'text/xml');
  }

  return xmlDoc;
}

/**
 * Converts a qualified XML name such as 'atom:summary' into its equivalent
 * JSON-friendly name such as 'atom$summary'. Optionally applies a given
 * namespace if none is defined.
 * @param {string} name The qualified node name.
 * @param {string} [opt_namespace] An optional namespace to apply to the given
 *     name. If name is 'xmlns', the namespace is applied after the name,
 *     producing something like 'xmlns$foo'.
 */
function jsonifyName_(name, opt_namespace) {
  name = name.replace(/:/g, '$');
  if (name.indexOf('$') < 0 && opt_namespace) {
    if (name == 'xmlns')
      name = name + '$' + opt_namespace;
    else
      name = opt_namespace + '$' + name;
  }

  return name;
}

/**
 * Converts an XML node into its JSON representation, optionally applying
 * a namespace to each element under the DOM.
 * @param {Node} xmlNode The XML node to convert to JSON.
 * @param {string} [opt_namespace] An optional namespace to apply to the
 *     resulting JSON.
 * @return {string} A JS object representing the given node.
 */
function xmlNodeToJson(xmlNode, opt_namespace) {
  var obj = {};
  var i = 0;

  var textContent = [];

  if (xmlNode.attributes) {
    for (i = 0; i < xmlNode.attributes.length; i++) {
      obj[jsonifyName_(xmlNode.attributes[i].nodeName, opt_namespace)] =
          xmlNode.attributes[i].nodeValue;
    }
  }

  if (xmlNode.firstChild) {
    for (i = 0; i < xmlNode.childNodes.length; i++) {
      var child = xmlNode.childNodes[i];
      var jsName = jsonifyName_(child.nodeName, opt_namespace);

      switch (child.nodeType) {
        case 4: // cdata
        case 3: //text
          textContent.push(child.nodeValue);
          break;

        case 2: // attribute
          obj[jsName] = child.nodeValue;
          break;

        case 1: // element
          var childJson = xmlNodeToJson(child, opt_namespace);
          if (jsName in obj) {
            obj[jsName] = listify(obj[jsName]);
            obj[jsName].push(childJson);
          } else {
            obj[jsName] = childJson;
          }
          break;
      }
    }
  }

  if (textContent.length) {
    textContent = textContent.join('');
    if (!textContent.match(/^\s+$/))
      obj.$t = textContent.replace(/^\s+/, ' ').replace(/\s+$/, ' ');
  }

  return obj;
}


/**
 * Determines if an object appears to be a list.
 * @param {object} obj Any object.
 * @return {boolean} True iff obj seems to be a list.
 */
function isList(obj) {
  return (typeof obj == 'object' && 'splice' in obj &&
          typeof obj.length == 'number');
}

/**
 * Possibly wraps an object in a list.
 * @param {object} obj Any object or list.
 * @return {list} List containing the single element, obj, or obj if it is
 *     already a list.
 */
function listify(obj) {
  return (isList(obj)) ? obj : [obj];
}
