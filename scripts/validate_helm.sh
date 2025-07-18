#!/bin/bash

# Legal AI Helm Chart Validation Script
# ΔΣ::Cursor - Pre-deployment validation

set -e

CHART_PATH="helm/legal-ai"
NAMESPACE="legal-ai-dev"

echo "🏗️ Legal AI Helm Chart Validation"
echo "=================================="

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm 3.0+"
    exit 1
fi

echo "✅ Helm version: $(helm version --short)"

# Validate chart syntax
echo "🔍 Validating chart syntax..."
if helm lint $CHART_PATH; then
    echo "✅ Chart syntax validation passed"
else
    echo "❌ Chart syntax validation failed"
    exit 1
fi

# Template validation
echo "🔍 Validating templates..."
if helm template legal-ai $CHART_PATH --debug > /dev/null; then
    echo "✅ Template validation passed"
else
    echo "❌ Template validation failed"
    exit 1
fi

# Dry run validation
echo "🔍 Performing dry run..."
if helm install legal-ai $CHART_PATH --dry-run --debug > /dev/null; then
    echo "✅ Dry run validation passed"
else
    echo "❌ Dry run validation failed"
    exit 1
fi

# Check required values
echo "🔍 Checking required values..."
REQUIRED_VALUES=(
    "api.enabled"
    "postgres.enabled"
    "redis.enabled"
    "global.namespace"
)

for value in "${REQUIRED_VALUES[@]}"; do
    if helm template legal-ai $CHART_PATH | grep -q "$value"; then
        echo "✅ Required value present: $value"
    else
        echo "❌ Required value missing: $value"
    fi
done

# Generate manifest for review
OUTPUT_DIR="helm/manifests"
mkdir -p $OUTPUT_DIR

echo "📝 Generating manifests to $OUTPUT_DIR..."
helm template legal-ai $CHART_PATH \
    --namespace $NAMESPACE \
    --output-dir $OUTPUT_DIR

echo "✅ Manifests generated successfully"

# Check for common issues
echo "🔍 Checking for common issues..."

# Check for resource specifications
if grep -r "resources:" $OUTPUT_DIR > /dev/null; then
    echo "✅ Resource specifications found"
else
    echo "⚠️  No resource specifications found"
fi

# Check for health checks
if grep -r "livenessProbe\|readinessProbe" $OUTPUT_DIR > /dev/null; then
    echo "✅ Health checks found"
else
    echo "⚠️  No health checks found"
fi

# Check for security context
if grep -r "securityContext" $OUTPUT_DIR > /dev/null; then
    echo "✅ Security context found"
else
    echo "⚠️  No security context found"
fi

echo ""
echo "🎯 Validation Summary"
echo "===================="
echo "Chart Path: $CHART_PATH"
echo "Namespace: $NAMESPACE"
echo "Generated Manifests: $OUTPUT_DIR"
echo ""
echo "✅ Helm chart validation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review generated manifests in $OUTPUT_DIR"
echo "2. Test installation: helm install legal-ai $CHART_PATH --namespace $NAMESPACE --create-namespace"
echo "3. Monitor deployment: kubectl get pods -n $NAMESPACE"
echo ""

# Cleanup option
read -p "🗑️  Remove generated manifests? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf $OUTPUT_DIR
    echo "✅ Generated manifests cleaned up"
fi 