package saml.akamai

import dispatch.implyRequestHandlerTuple
import dispatch.implyRequestVerbs

case class AkamaiCCU(username: String, password: String,
  email: String = "",
  domain: String = "production",
  action: String = "remove",
  endpoint: String = "https://ccuapi.akamai.com:443/soap/servlet/soap/purge") {

  private val defaultOptions =
    if (!email.isEmpty()) List(<element xsi:type="xsd:string">email-notification={ email }</element>)
    else List()

  private val options =
    <element xsi:type="xsd:string">action={ action }</element> ::
      <element xsi:type="xsd:string">domain={ domain }</element> :: defaultOptions

  def buildPurgeRequestXml(urls: Seq[String]) = {
    val urlsXml = (for {
      url <- urls
      if (!url.isEmpty())
    } yield <element xsi:type="xsd:string">{ url }</element>)

    <soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:pur="http://www.akamai.com/purge" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
      <soapenv:Header/>
      <soapenv:Body>
        <pur:purgeRequest soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <name xsi:type="xsd:string">{ username }</name>
          <pwd xsi:type="xsd:string">{ password }</pwd>
          <opt xsi:type="pur:ArrayOfString" soapenc:arrayType={ "xsd:string[%d]".format(options.length) }>
            { options }
          </opt>
          <uri xsi:type="pur:ArrayOfString" soapenc:arrayType={ "xsd:string[%d]".format(urlsXml.length) }>
            { urlsXml }
          </uri>
        </pur:purgeRequest>
      </soapenv:Body>
    </soapenv:Envelope>
  }

  def makePurgeRequest(urls: Seq[String]) = {
    val xml = buildPurgeRequestXml(urls)
    val request = dispatch.url(endpoint).POST << xml.toString <:< Map(
      "Content-Type" -> """text/xml; charset="utf-8"""",
      "SOAPAction" -> "PurgeRequest")
    dispatch.Http(request > dispatch.as.xml.Elem)
  }

  //  def request(urls: List[String]) = {
  //    val xml = buildXml(urls)
  //    //val service = dispatch.url(endpoint)
  //    //dispatch.Http(service)
  //    val url = new java.net.URL(endpoint)
  //    val conn = url.openConnection().asInstanceOf[javax.net.ssl.HttpsURLConnection]
  //    conn.setDoOutput(true)
  //    conn.setDoInput(true)
  //    conn.setRequestProperty("Content-Type", "text/xml; charset=utf-8")
  //    conn.setRequestProperty("Content-Length", xml.length.toString)
  //    conn.setRequestProperty("SOAPAction", "PurgeRequest")
  //    conn.setRequestMethod("POST")
  //    val ostream = new java.io.OutputStreamWriter(conn.getOutputStream(), "UTF-8")
  //    ostream.write(xml.toString)
  //    ostream.flush()
  //    ostream.close()
  //    
  //    val input = if (conn.getResponseCode() >= 400)
  //  }

}

object AkamaiCCU {
  //private def tryFinally[A, B](code: A => B)(cleanUp: A => Any)

  private def cleanupThis[A, B](x: => A)(f: A => B)(cleanup: A => Any): B =
    try {
      f(x)
    } finally {
      cleanup(x)
    }

  private def loadProp(propFilePath: String): java.util.Properties = {
    val props = new java.util.Properties()
    try {
      val file = new java.io.File(propFilePath)
      cleanupThis(new java.io.InputStreamReader(new java.io.FileInputStream(file), "UTF-8")) {
        reader => props.load(reader)
      } {
        reader => reader.close()
      }
    }
    props
  }
  def main(args: Array[String]) = {
    val props = loadProp(args(0))
    val username = props.getProperty("akamai.username", "")
    val password = props.getProperty("akamai.password", "")
    val email = props.getProperty("akamai.email", "")
    println(email)
    val ccuapi = AkamaiCCU(username, password, email = email)
    println(ccuapi.buildPurgeRequestXml(args.tail))

    val promise = ccuapi.makePurgeRequest(args.tail)
    val xml = promise()
    println(xml)
    println((xml \\ "resultCode")(0).text)
    println((xml \\ "resultMsg")(0).text)
  }
}

// vim: set ts=4 sw=4 et:
