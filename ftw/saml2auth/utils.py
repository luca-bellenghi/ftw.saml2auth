from DateTime import DateTime
from dm.saml2.pyxb import assertion as saml
from dm.saml2.pyxb import protocol as samlp
from dm.saml2.pyxb.protocol import Response
from dm.saml2.signature import SignatureContext
from pyxb.bundles.wssplat import ds
from pyxb.utils.domutils import BindingDOMSupport
import dm.xmlsec.binding as xmlsec

BindingDOMSupport.DeclareNamespace(samlp.Namespace, 'samlp')
BindingDOMSupport.DeclareNamespace(saml.Namespace, 'saml')
BindingDOMSupport.DeclareNamespace(ds.Namespace, 'ds')


def create_saml_response(in_response_to, destination, issuer_id, subject,
                         subject_format, audience, attributes={}, key=''):
    """Construct a SAML Response."""

    resp = Response(
        InResponseTo=in_response_to,
        Destination=destination,
    )

    now = DateTime()

    resp.Issuer = saml.Issuer(issuer_id)
    resp.Status = samlp.Status(samlp.StatusCode(
        Value=u'urn:oasis:names:tc:SAML:2.0:status:Success'))

    assertion = saml.Assertion()
    assertion.Issuer = saml.Issuer(issuer_id)

    assertion.Subject = saml.Subject()
    assertion.Subject.NameID = saml.NameID(subject, Format=subject_format)
    assertion.Subject.SubjectConfirmation = [saml.SubjectConfirmation(
        saml.SubjectConfirmationData(
            InResponseTo=in_response_to,
            NotOnOrAfter=(now + 1.0/24).HTML4(),
            Recipient=destination,
        ),
        Method="urn:oasis:names:tc:SAML:2.0:cm:bearer")]

    assertion.Conditions = saml.Conditions(
        NotBefore=now.HTML4(),
        NotOnOrAfter=(now + 1.0/24).HTML4())
    assertion.Conditions.AudienceRestriction = [saml.AudienceRestriction(
        saml.Audience(audience)
    )]

    assertion.AuthnStatement = [saml.AuthnStatement(
        saml.AuthnContext(saml.AuthnContextClassRef(
            u'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport')),
        AuthnInstant=now.HTML4(),
        SessionIndex=assertion.ID,
    )]

    if attributes:
        assertion.AttributeStatement = [saml.AttributeStatement()]
        for k, v in attributes.items():
            assertion.AttributeStatement[0].append(
                saml.Attribute(
                    saml.AttributeValue(v),
                    Name=k,
                )
            )

    resp.Assertion = [assertion]

    if key:
        # Sign assertion
        sign_context = SignatureContext()
        key = xmlsec.Key.loadMemory(key, xmlsec.KeyDataFormatPem, None)
        sign_context.add_key(key, issuer_id)
        assertion.request_signature(context=sign_context)

    return resp.toxml()
