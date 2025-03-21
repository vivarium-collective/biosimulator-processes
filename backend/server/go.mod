module github.com/vivarium-collective/biosimulator-processes/backend/server

go 1.24.1

replace github.com/vivarium-collective/biosimulator-processes/backend/shared => ../shared

replace github.com/vivarium-collective/biosimulator-processes/backend/proto => ../proto

require github.com/vivarium-collective/biosimulator-processes/backend/shared v0.0.0-00010101000000-000000000000
