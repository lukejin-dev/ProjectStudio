import xml.dom.minidom as minidom

def XmlList(Dom, String):
  """Get a list of XML Elements using XPath style syntax."""
  if String == None or String == "" or Dom == None or Dom == "":
    return []
  if Dom.nodeType==Dom.DOCUMENT_NODE:
    Dom = Dom.documentElement
  if String[0] == "/":
    String = String[1:]
  tagList = String.split('/')
  nodes = [Dom]
  index = 0
  end = len(tagList) - 1
  while index <= end:
    childNodes = []
    for node in nodes:
      if node.nodeType == node.ELEMENT_NODE and node.tagName == tagList[index]:
        if index < end:
          childNodes.extend(node.childNodes)
        else:
          childNodes.append(node)
    nodes = childNodes
    childNodes = []
    index += 1

  return nodes

def XmlNode (Dom, String):
  """Return a single node that matches the String which is XPath style syntax."""
  if String == None or String == ""  or Dom == None or Dom == "":
    return ""
  if Dom.nodeType==Dom.DOCUMENT_NODE:
    Dom = Dom.documentElement
  if String[0] == "/":
    String = String[1:]
  tagList = String.split('/')
  index = 0
  end = len(tagList) - 1
  childNodes = [Dom]
  while index <= end:
    for node in childNodes:
      if node.nodeType == node.ELEMENT_NODE and node.tagName == tagList[index]:
        if index < end:
          childNodes = node.childNodes
        else:
          return node
        break
    index += 1
  return ""

def XmlElement (Dom, String):
  """Return a single element that matches the String which is XPath style syntax."""
  try:
    return XmlNode (Dom, String).firstChild.data.strip()
  except:
    return ''

def XmlElementData (Dom):
  """Get the text for this element."""
  if Dom == None or Dom == '' or Dom.firstChild == None:
    return ''
  return Dom.firstChild.data.strip()        
        