# CertMon
A simple utility for monitoring certificate expiration with VCF Operaions. 

Pulls certificates from a list of URLs and reports their names and expiration time to VCF Operations.

Typical use case is to run it on a daily basis using some scheduler, such as cron.

## VCF Ops resource
* Resource type: CustomCertificate
* Properties: name - Certificate subject
* Metrics: daysToExiry - Number of days before certificate expires

## Usage
``bash
python -c <configfile>
```

## Sample Config File
```yaml
ops_host: "10.0.0.10"       # VCF Ops Host
ops_username: "admin"       # VCF Ops Username
ops_auth_source: "LOCAL"    # VCF Ops Authentication source
ops_password: "***"         # VCF Ops Password

sites:                      # URLs to monitor
  - www.google.com
  - broadcom.com
  - whitehouse.gov
  - www.vmware.com
```