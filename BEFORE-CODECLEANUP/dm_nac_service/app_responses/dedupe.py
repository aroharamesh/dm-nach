# Fake Response of Dedupe
dedupe_response_data = \
    [
        {
            "dedupeRequestSource": {
                "loanId": "12345",
                "customerName": "Priya",
                "dateOfBirth": "1999-09-17",
                "contactNumber": "8637493732",
                "kycDetailsList": [
                    {
                        "type": "AADHARCARD",
                        "value": "********0076"
                    }
                ],
            "accountNumber": "abcd",
            "pincode": "12345"
        },
        "results": [
            {
                "attribute": "null",
                "value": "NAME",
                "ruleName": "Dedupe Secondary First Pass",
                "id": "null",
                "isEligible": "false",
                "message": "Secondary Duplication Detected"
            }
        ],
        "type": "SECONDARY_ONE",
        "dedupeReferenceId": 5211201547885960,
        "isDedupePresent": "true",
        "referenceLoan": {
            "originatorId": "U67120MH1980PTC023349",
            "sectorId": 3,
            "maxDpd": 0.0,
            "firstName": "Priyanka Vaijinath Suryawanshi",
            "dateOfBirth": "2001-01-01",
            "mobilePhone": "8698347859",
            "accountNumber": "34874801855"
        }
    }
]