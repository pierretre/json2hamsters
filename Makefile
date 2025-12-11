# Makefile for converting JSON -> .hmst using `main.py`
# and .hmst -> JSON using `hmst2json.py`

# Path constants (override on command line if needed)
VENV_PYTHON ?= ./venv/bin/python
SCRIPT ?= main.py
REVERSE_SCRIPT ?= hmst2json.py
INPUT_DIR ?= /home/pierre/1-projects/1-Git/task-modeling-for-interactive-dt/scenarios/fisher-techniks
OUTPUT_DIR ?= /home/pierre/1-projects/1-Git/task-modeling-for-interactive-dt/task-models/ft/src/tasks/Operator

# Discover JSONs and scenario names (basenames without extension)
JSONS := $(wildcard $(INPUT_DIR)/*.json)
SCENARIOS := $(notdir $(basename $(JSONS)))
HMSTS := $(patsubst $(INPUT_DIR)/%.json,$(OUTPUT_DIR)/%.hmst,$(JSONS))

# For reverse conversion (HMST -> JSON)
HMST_INPUT_DIR ?= $(OUTPUT_DIR)
JSON_OUTPUT_DIR ?= generated/reverse
HMST_FILES := $(wildcard $(HMST_INPUT_DIR)/*.hmst)
REVERSE_JSONS := $(patsubst $(HMST_INPUT_DIR)/%.hmst,$(JSON_OUTPUT_DIR)/%.json,$(HMST_FILES))

.PHONY: all list clean reverse clean-reverse test-reverse $(SCENARIOS)

# Default: build all .hmst files for JSONs found in INPUT_DIR
all: $(HMSTS)

# Reverse: convert all .hmst files back to JSON
reverse: $(REVERSE_JSONS)

# Test reverse conversion on generated files
test-reverse:
	mkdir -p $(JSON_OUTPUT_DIR)
	$(VENV_PYTHON) $(REVERSE_SCRIPT) generated/test.hmst -o $(JSON_OUTPUT_DIR)/test.json

# Allow calling `make Scenario.2b` which will convert the matching JSON
%: $(INPUT_DIR)/%.json
	mkdir -p $(OUTPUT_DIR)
	$(VENV_PYTHON) $(SCRIPT) $(INPUT_DIR)/$*.json -o $(OUTPUT_DIR)/$*.hmst

# Also keep explicit file target rule in case someone references the output path
$(OUTPUT_DIR)/%.hmst: $(INPUT_DIR)/%.json
	mkdir -p $(dir $@)
	$(VENV_PYTHON) $(SCRIPT) $< -o $@

# Rule for reverse conversion: .hmst -> .json
$(JSON_OUTPUT_DIR)/%.json: $(HMST_INPUT_DIR)/%.hmst
	mkdir -p $(dir $@)
	$(VENV_PYTHON) $(REVERSE_SCRIPT) $< -o $@

list:
	@echo "Input dir: $(INPUT_DIR)"
	@echo "Output dir: $(OUTPUT_DIR)"
	@echo "Found scenarios:"
	@printf "  %s\n" $(SCENARIOS)
	@echo ""
	@echo "Reverse conversion:"
	@echo "  HMST input dir: $(HMST_INPUT_DIR)"
	@echo "  JSON output dir: $(JSON_OUTPUT_DIR)"

clean:
	rm -f $(HMSTS)

clean-reverse:
	rm -rf $(JSON_OUTPUT_DIR)
