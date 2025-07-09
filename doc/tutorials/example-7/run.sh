powerconf render CONFIG-1.yaml ACME-CONFIG-TEMPLATE.ini _acmi-1.ini
powerconf render CONFIG-2.yaml ACME-CONFIG-TEMPLATE.ini _acmi-2

powerconf generate CONFIG-1.yaml _acmi-1.yaml --node acme
powerconf generate CONFIG-2.yaml _acmi-2.yaml --node acme

powerconf generate CONFIG-1.yaml _acmi-1.json --node acme --format json
powerconf generate CONFIG-2.yaml _acmi-2.json --node acme --format json
