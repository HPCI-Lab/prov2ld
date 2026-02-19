
<div align="center">
  <a href="https://github.com/HPCI-Lab">
    <img src="./assets/HPCI-Lab.png" alt="HPCI Lab Logo" width="100" height="100">
  </a>

  <h3 align="center">prov2ld</h3>

  <p align="center">
    A lightweight Python script to convert PROV-JSON documents to PROV-JSONLD format according to the W3C PROV-JSONLD specification.
    <br />
    <a href="https://github.com/HPCI-Lab/prov2ld/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/HPCI-Lab/prov2ld/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<br />

<div align="center">
  
[![Contributors](https://img.shields.io/github/contributors/HPCI-Lab/prov2ld?style=for-the-badge)](https://github.com/HPCI-Lab/prov2ld/graphs/contributors)
[![Forks](https://img.shields.io/github/forks/HPCI-Lab/prov2ld?style=for-the-badge)](https://github.com/HPCI-Lab/prov2ld/network/members)
[![Stars](https://img.shields.io/github/stars/HPCI-Lab/prov2ld?style=for-the-badge)](https://github.com/HPCI-Lab/prov2ld/stargazers)
[![Issues](https://img.shields.io/github/issues/HPCI-Lab/prov2ld?style=for-the-badge)](https://github.com/HPCI-Lab/prov2ld/issues)
[![GPLv3 License](https://img.shields.io/badge/LICENCE-GPL3.0-green?style=for-the-badge)](https://opensource.org/licenses/)

</div>

## Requirements

For the `ld2viz` command, the library requires the [GraphViz](https://graphviz.org/) suite. For everything to correctly work, this module has to be installed. 
We reference both the [installation section on their docs](https://graphviz.org/download/), as well as the main ways to install it. 

#### Linux

```bash
sudo apt install graphviz
```

#### MacOS

```bash
# Installing Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install graphviz
```

#### Windows

Installers are at the [Download page of GraphViz](https://graphviz.org/download/). 

## Installation

```bash
pip install prov2ld
```

## Basic Usage

### 1. Convert a file to Prov-JSONLD

```bash
python -m prov2ld input.json output.jsonld
# Basic example from the PROV-PRIMER
python -m prov2ld example/test_comprehensive.json example/test_comprehensive.jsonld
```

### 2. Convert Prov-JSONLD to Graph Visualization

```bash
python -m ld2viz input.jsonld output.png
# Or: 
python -m prov2ld example/test_comprehensive.jsonld example/test_comprehensive.png
```

## What Gets Converted?

### Input (PROV-JSON)
```json
{
  "prefix": {
    "ex": "http://example.org/",
    "prov": "http://www.w3.org/ns/prov#"
  },
  "entity": {
    "ex:e1": {}
  },
  "activity": {
    "ex:a1": {}
  },
  "wasGeneratedBy": {
    "_:gen1": {
      "prov:entity": "ex:e1",
      "prov:activity": "ex:a1"
    }
  }
}
```

### Output (PROV-JSONLD)
```json
{
  "@context": [
    {
      "ex": "http://example.org/",
      "prov": "http://www.w3.org/ns/prov#"
    },
    "https://openprovenance.org/prov-jsonld/context.json"
  ],
  "@graph": [
    {
      "@type": "prov:Entity",
      "@id": "ex:e1"
    },
    {
      "@type": "prov:Activity",
      "@id": "ex:a1"
    },
    {
      "@type": "prov:Generation",
      "@id": "_:gen1",
      "entity": "ex:e1",
      "activity": "ex:a1"
    }
  ]
}
```

## PROV Elements Supported

### Core Elements
- **Entities** (`prov:Entity`)
- **Activities** (`prov:Activity`)
- **Agents** (`prov:Agent`)

### Relations
- **Generation** (`prov:Generation`) - `wasGeneratedBy`
- **Usage** (`prov:Usage`) - `used`
- **Communication** (`prov:Communication`) - `wasInformedBy`
- **Start** (`prov:Start`) - `wasStartedBy`
- **End** (`prov:End`) - `wasEndedBy`
- **Invalidation** (`prov:Invalidation`) - `wasInvalidatedBy`
- **Derivation** (`prov:Derivation`) - `wasDerivedFrom`
- **Attribution** (`prov:Attribution`) - `wasAttributedTo`
- **Association** (`prov:Association`) - `wasAssociatedWith`
- **Delegation** (`prov:Delegation`) - `actedOnBehalfOf`
- **Influence** (`prov:Influence`) - `wasInfluencedBy`
- **Specialization** (`provext:Specialization`) - `specializationOf`
- **Alternate** (`provext:Alternate`) - `alternateOf`
- **Membership** (`provext:Membership`) - `hadMember`

### Additional Features
- Custom attributes with namespaces
- Typed values
- Language-tagged strings
- Time attributes (startTime, endTime, time)
- PROV bundles
- Roles, types, labels, and locations

## Support

This converter implements the PROV-JSONLD specification from:
*Moreau, L., & Huynh, T. D. (2021). The PROV-JSONLD Serialization*

For questions about PROV itself, see: 

- [PROV Overview](https://www.w3.org/TR/prov-overview/)
- [PROV-DM Specification](https://www.w3.org/TR/prov-dm/)
- [PROV-O Ontology](https://www.w3.org/TR/prov-o/)
- [PROV-JSON Submission](https://www.w3.org/Submission/prov-json/)
- [JSON-LD 1.1 Specification](https://www.w3.org/TR/json-ld11/)
- [PROV-JSONLD Context](https://openprovenance.org/prov-jsonld/context.json)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
