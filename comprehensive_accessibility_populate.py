#!/usr/bin/env python3
"""
Comprehensive accessibility patterns population for all frameworks and WCAG levels
"""

import os
import sys
import hashlib
from datetime import datetime

# Add the docs-mcp directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Also add the virtual environment if needed
VENV_SITE_PACKAGES = os.path.join(SCRIPT_DIR, 'venv', 'lib', 'python3.11', 'site-packages')
if os.path.exists(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)

def populate_comprehensive_accessibility_patterns():
    """Add comprehensive accessibility patterns covering all frameworks and WCAG levels"""
    
    print("🔧 Populating Comprehensive Accessibility Patterns Database")
    print("=" * 80)
    
    try:
        from server import initialize_chroma
        
        # Initialize connection
        if not initialize_chroma():
            print("❌ Failed to connect to database")
            return False
        
        # Import collection after initialization
        from server import collection
        
        if not collection:
            print("❌ Collection not available")
            return False
        
        def generate_doc_id(content, framework):
            """Generate a unique document ID"""
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            return f"{framework}_{content_hash}"
        
        def add_pattern_direct(pattern_content, target_framework, wcag_level, category, source):
            """Add pattern directly to collection"""
            doc_id = generate_doc_id(pattern_content, f"accessibility_{target_framework}")
            
            metadata = {
                "framework": "accessibility",
                "target_framework": target_framework,
                "wcag_level": wcag_level,
                "category": category,
                "source": source,
                "type": "accessibility_pattern",
                "project": "general",
                "added_at": datetime.now().isoformat(),
                "content_hash": hashlib.md5(pattern_content.encode()).hexdigest()
            }
            
            collection.add(
                documents=[pattern_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return f"✅ Added {target_framework} {category} pattern (WCAG {wcag_level})"
        
        # Comprehensive accessibility patterns covering all frameworks and scenarios
        patterns = [
            # FastAPI - WCAG A Level
            {
                "content": """
# FastAPI WCAG Level A Accessibility Patterns

## Basic Form Accessibility
```python
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/form", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "form_title": "Product Analysis Form",
        "form_description": "Upload an image to analyze product value"
    })

# Basic accessible form handling
@app.post("/analyze")
async def analyze_product(
    product_name: str = Form(..., description="Name of the product"),
    condition: str = Form(..., description="Product condition"),
    image: UploadFile = File(..., description="Product image")
):
    # Ensure required fields have descriptive names
    if not product_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Product name is required for analysis"
        )
    
    return {"message": "Analysis started", "product": product_name}
```

## HTML Template Structure (WCAG A)
```html
<!-- templates/form.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <main>
        <h1>{{ form_title }}</h1>
        <p>{{ form_description }}</p>
        
        <form method="post" action="/analyze" enctype="multipart/form-data">
            <label for="product_name">Product Name:</label>
            <input type="text" id="product_name" name="product_name" required>
            
            <label for="condition">Condition:</label>
            <select id="condition" name="condition" required>
                <option value="">Select condition</option>
                <option value="new">New</option>
                <option value="used">Used</option>
                <option value="damaged">Damaged</option>
            </select>
            
            <label for="image">Product Image:</label>
            <input type="file" id="image" name="image" accept="image/*" required>
            
            <button type="submit">Analyze Product</button>
        </form>
    </main>
</body>
</html>
```
                """,
                "target_framework": "fastapi",
                "wcag_level": "A",
                "category": "forms",
                "source": "WCAG 2.2 Level A guidelines"
            },
            
            # FastAPI - WCAG AA Level  
            {
                "content": """
# FastAPI WCAG Level AA Accessibility Patterns

## Enhanced Form Validation with ARIA
```python
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional

class AccessibleErrorResponse(BaseModel):
    field: str
    message: str
    error_code: str
    aria_live: str = "polite"
    focus_target: Optional[str] = None

class ProductAnalysisForm(BaseModel):
    product_name: str = Field(
        ..., 
        min_length=2,
        max_length=100,
        description="Product name for analysis"
    )
    condition: str = Field(
        ...,
        description="Product condition assessment"
    )
    
    @validator('condition')
    def validate_condition(cls, v):
        valid_conditions = ['new', 'like-new', 'good', 'fair', 'poor']
        if v not in valid_conditions:
            raise ValueError('Invalid condition selection')
        return v

@app.post("/analyze")
async def analyze_product_enhanced(
    request: Request,
    product_name: str = Form(...),
    condition: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        # Validate form data
        form_data = ProductAnalysisForm(
            product_name=product_name,
            condition=condition
        )
        
        # Image validation
        if not image.content_type.startswith('image/'):
            return JSONResponse(
                status_code=422,
                content=AccessibleErrorResponse(
                    field="image",
                    message="Please upload a valid image file (JPEG, PNG, or WebP)",
                    error_code="INVALID_IMAGE_TYPE",
                    focus_target="image"
                ).dict()
            )
        
        # Process analysis
        result = await process_analysis(form_data, image)
        
        return {
            "success": True,
            "message": f"Analysis completed for {form_data.product_name}",
            "result": result,
            "accessibility": {
                "announce": f"Analysis completed. Product value estimated at {result.get('value', 'unknown')}"
            }
        }
        
    except ValidationError as e:
        # Return accessible error responses
        errors = []
        for error in e.errors():
            field_name = error['loc'][0] if error['loc'] else 'form'
            errors.append(AccessibleErrorResponse(
                field=field_name,
                message=error['msg'],
                error_code="VALIDATION_ERROR",
                focus_target=field_name
            ))
        
        return JSONResponse(
            status_code=422,
            content={"errors": [error.dict() for error in errors]}
        )
```

## Enhanced HTML Template (WCAG AA)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ form_title }} - ResaleAnalyzer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Upload product images for AI-powered resale value analysis">
    <style>
        /* WCAG AA Color Contrast (4.5:1 minimum) */
        :root {
            --primary-color: #1a365d;    /* 7.23:1 contrast */
            --error-color: #742a2a;     /* 5.12:1 contrast */
            --success-color: #22543d;   /* 5.74:1 contrast */
            --text-color: #1a202c;      /* 16.75:1 contrast */
            --bg-color: #ffffff;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui;
            color: var(--text-color);
            background-color: var(--bg-color);
            line-height: 1.5;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .required::after {
            content: " *";
            color: var(--error-color);
        }
        
        input, select {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e2e8f0;
            border-radius: 0.375rem;
            font-size: 1rem;
        }
        
        input:focus, select:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
            border-color: var(--primary-color);
        }
        
        .error {
            color: var(--error-color);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .help-text {
            font-size: 0.875rem;
            color: #4a5568;
            margin-top: 0.25rem;
        }
        
        button {
            background-color: var(--primary-color);
            color: var(--bg-color);
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.375rem;
            font-size: 1rem;
            cursor: pointer;
        }
        
        button:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        button:hover {
            background-color: #2c5282;
        }
    </style>
</head>
<body>
    <main>
        <h1>{{ form_title }}</h1>
        <p>{{ form_description }}</p>
        
        <form method="post" action="/analyze" enctype="multipart/form-data" novalidate>
            <div class="form-group">
                <label for="product_name" class="required">Product Name</label>
                <input 
                    type="text" 
                    id="product_name" 
                    name="product_name" 
                    required 
                    aria-describedby="product_name_help product_name_error"
                    autocomplete="off"
                >
                <div id="product_name_help" class="help-text">
                    Enter the brand and model of your product (e.g., "Nike Air Max 90")
                </div>
                <div id="product_name_error" class="error" aria-live="polite"></div>
            </div>
            
            <div class="form-group">
                <label for="condition" class="required">Product Condition</label>
                <select 
                    id="condition" 
                    name="condition" 
                    required 
                    aria-describedby="condition_help condition_error"
                >
                    <option value="">Select condition</option>
                    <option value="new">New with tags/box</option>
                    <option value="like-new">Like new</option>
                    <option value="good">Good condition</option>
                    <option value="fair">Fair condition</option>
                    <option value="poor">Poor condition</option>
                </select>
                <div id="condition_help" class="help-text">
                    Choose the condition that best describes your item's current state
                </div>
                <div id="condition_error" class="error" aria-live="polite"></div>
            </div>
            
            <div class="form-group">
                <label for="image" class="required">Product Image</label>
                <input 
                    type="file" 
                    id="image" 
                    name="image" 
                    accept="image/jpeg,image/png,image/webp" 
                    required 
                    aria-describedby="image_help image_error"
                >
                <div id="image_help" class="help-text">
                    Upload a clear photo showing the product and any relevant details
                </div>
                <div id="image_error" class="error" aria-live="polite"></div>
            </div>
            
            <button type="submit">Analyze Product Value</button>
        </form>
        
        <div id="results" aria-live="polite" aria-label="Analysis results"></div>
    </main>
    
    <script>
        // Accessible form validation
        document.querySelector('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Clear previous errors
            document.querySelectorAll('.error').forEach(el => el.textContent = '');
            
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('results').innerHTML = 
                        `<p role="status">${result.accessibility.announce}</p>`;
                } else {
                    // Display accessible error messages
                    if (result.errors) {
                        result.errors.forEach(error => {
                            const errorElement = document.getElementById(`${error.field}_error`);
                            if (errorElement) {
                                errorElement.textContent = error.message;
                                if (error.focus_target) {
                                    document.getElementById(error.focus_target).focus();
                                }
                            }
                        });
                    }
                }
            } catch (error) {
                document.getElementById('results').innerHTML = 
                    '<p role="alert">An error occurred. Please try again.</p>';
            }
        });
    </script>
</body>
</html>
```
                """,
                "target_framework": "fastapi",
                "wcag_level": "AA",
                "category": "forms",
                "source": "WCAG 2.2 Level AA guidelines"
            },
            
            # Swift iOS - WCAG A Level
            {
                "content": """
# Swift iOS WCAG Level A Accessibility Patterns

## Basic VoiceOver Support
```swift
import SwiftUI

struct BasicAccessibleView: View {
    let product: Product
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Basic image accessibility
            AsyncImage(url: product.imageURL) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fit)
            } placeholder: {
                ProgressView()
            }
            .frame(height: 200)
            .accessibilityLabel(product.imageDescription)
            
            // Basic text accessibility
            Text(product.name)
                .font(.title2)
                .accessibilityAddTraits(.isHeader)
            
            Text(product.description)
                .font(.body)
            
            Text("$\\(product.price, specifier: "%.2f")")
                .font(.title3)
                .foregroundColor(.green)
                .accessibilityLabel("Price: \\(product.price, specifier: "%.2f") dollars")
        }
        .padding()
    }
}

// Basic accessible button
struct AccessibleActionButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .background(Color.blue)
                .cornerRadius(8)
        }
        .accessibilityLabel(title)
        .accessibilityHint("Double tap to perform action")
    }
}

// Basic accessible form
struct BasicAccessibleForm: View {
    @State private var productName = ""
    @State private var condition = "good"
    
    let conditions = ["new", "good", "fair", "poor"]
    
    var body: some View {
        Form {
            Section("Product Details") {
                TextField("Product name", text: $productName)
                    .accessibilityLabel("Product name")
                    .accessibilityHint("Enter the name of your product")
                
                Picker("Condition", selection: $condition) {
                    ForEach(conditions, id: \\.self) { condition in
                        Text(condition.capitalized)
                    }
                }
                .accessibilityLabel("Product condition")
                .accessibilityHint("Select the current condition of your product")
            }
        }
        .navigationTitle("Add Product")
        .accessibilityElement(children: .contain)
    }
}
```

## Basic Navigation Accessibility
```swift
struct AccessibleNavigationView: View {
    var body: some View {
        NavigationView {
            List {
                NavigationLink("Recent Analysis") {
                    RecentAnalysisView()
                }
                .accessibilityLabel("Recent Analysis")
                .accessibilityHint("View your recent product analyses")
                
                NavigationLink("Upload New Product") {
                    UploadView()
                }
                .accessibilityLabel("Upload New Product")
                .accessibilityHint("Upload a new product for analysis")
                
                NavigationLink("Settings") {
                    SettingsView()
                }
                .accessibilityLabel("Settings")
                .accessibilityHint("Adjust app settings and preferences")
            }
            .navigationTitle("ResaleAnalyzer")
            .accessibilityElement(children: .contain)
        }
    }
}
```
                """,
                "target_framework": "swift_ios",
                "wcag_level": "A",
                "category": "basic",
                "source": "iOS Accessibility Guidelines Level A"
            },
            
            # Swift iOS - WCAG AA Level
            {
                "content": """
# Swift iOS WCAG Level AA Accessibility Patterns

## Enhanced VoiceOver with Dynamic Type
```swift
import SwiftUI

struct EnhancedAccessibleAnalysisView: View {
    let analysisResult: AnalysisResult
    @Environment(\\.dynamicTypeSize) var dynamicTypeSize
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: adaptiveSpacing) {
            // Enhanced image accessibility with context
            AsyncImage(url: analysisResult.imageURL) { phase in
                switch phase {
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .accessibilityLabel(analysisResult.detailedImageDescription)
                        .accessibilityAddTraits(.isImage)
                        .accessibilityRemoveTraits(.isButton)
                case .failure(_):
                    Image(systemName: "photo")
                        .foregroundColor(.gray)
                        .accessibilityLabel("Image failed to load")
                case .empty:
                    ProgressView()
                        .accessibilityLabel("Loading product image")
                @unknown default:
                    EmptyView()
                }
            }
            .frame(maxHeight: dynamicImageHeight)
            
            // Enhanced product information with proper hierarchy
            VStack(alignment: .leading, spacing: 12) {
                Text(analysisResult.productName)
                    .font(.title2)
                    .fontWeight(.bold)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityHeading(.h1)
                    .dynamicTypeSize(.xSmall ... .accessibility3)
                
                Text(analysisResult.brand)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .accessibilityLabel("Brand: \\(analysisResult.brand)")
                
                // Enhanced price display with currency formatting
                HStack {
                    Text("Estimated Value:")
                        .font(.headline)
                        .accessibilityAddTraits(.isHeader)
                    
                    Spacer()
                    
                    Text(analysisResult.estimatedValue, format: .currency(code: "USD"))
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(.green)
                        .accessibilityLabel("Estimated value: \\(analysisResult.estimatedValue, format: .currency(code: "USD"))")
                }
                .padding(.vertical, 8)
                .background(Color(.systemGray6))
                .cornerRadius(8)
                .accessibilityElement(children: .combine)
                
                // Expandable details section
                DisclosureGroup("Analysis Details", isExpanded: $isExpanded) {
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(analysisResult.details, id: \\.id) { detail in
                            DetailRow(detail: detail)
                        }
                    }
                    .padding(.top, 8)
                }
                .accessibilityElement(children: .contain)
                .accessibilityLabel("Analysis details")
                .accessibilityHint(isExpanded ? "Collapse to hide details" : "Expand to show analysis details")
                
                // Confidence indicator with accessible representation
                ConfidenceIndicator(confidence: analysisResult.confidence)
                
                // Action buttons with enhanced accessibility
                HStack(spacing: 16) {
                    ShareButton(result: analysisResult)
                    SaveButton(result: analysisResult)
                }
                .padding(.top, 16)
            }
            .padding()
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Analysis results for \\(analysisResult.productName)")
        .accessibilityActions {
            Button("Share Analysis") {
                shareAnalysis()
            }
            Button("Save to Favorites") {
                saveToFavorites()
            }
        }
    }
    
    // Dynamic spacing based on accessibility settings
    private var adaptiveSpacing: CGFloat {
        switch dynamicTypeSize {
        case .xSmall, .small, .medium:
            return 16
        case .large, .xLarge, .xxLarge:
            return 20
        case .xxxLarge, .accessibility1, .accessibility2, .accessibility3, .accessibility4, .accessibility5:
            return 24
        @unknown default:
            return 16
        }
    }
    
    // Dynamic image height for accessibility
    private var dynamicImageHeight: CGFloat {
        switch dynamicTypeSize {
        case .accessibility1, .accessibility2, .accessibility3, .accessibility4, .accessibility5:
            return 150
        default:
            return 250
        }
    }
    
    private func shareAnalysis() {
        // Share implementation
    }
    
    private func saveToFavorites() {
        // Save implementation
    }
}

struct DetailRow: View {
    let detail: AnalysisDetail
    
    var body: some View {
        HStack {
            Text(detail.label)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(width: 100, alignment: .leading)
            
            Text(detail.value)
                .font(.subheadline)
                .fontWeight(.medium)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\\(detail.label): \\(detail.value)")
    }
}

struct ConfidenceIndicator: View {
    let confidence: Double
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Analysis Confidence")
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                ProgressView(value: confidence, total: 1.0)
                    .progressViewStyle(LinearProgressViewStyle(tint: confidenceColor))
                
                Text("\\(confidence * 100, specifier: "%.0f")%")
                    .font(.caption)
                    .fontWeight(.medium)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Analysis confidence: \\(confidence * 100, specifier: "%.0f") percent")
        .accessibilityValue(confidenceDescription)
    }
    
    private var confidenceColor: Color {
        switch confidence {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .orange
        default: return .red
        }
    }
    
    private var confidenceDescription: String {
        switch confidence {
        case 0.8...1.0: return "High confidence"
        case 0.6..<0.8: return "Medium confidence"
        default: return "Low confidence"
        }
    }
}

struct ShareButton: View {
    let result: AnalysisResult
    
    var body: some View {
        Button(action: shareAction) {
            Label("Share", systemImage: "square.and.arrow.up")
                .font(.headline)
        }
        .buttonStyle(.bordered)
        .accessibilityLabel("Share analysis")
        .accessibilityHint("Share the analysis results with others")
    }
    
    private func shareAction() {
        // Share implementation
    }
}

struct SaveButton: View {
    let result: AnalysisResult
    @State private var isSaved = false
    
    var body: some View {
        Button(action: saveAction) {
            Label(isSaved ? "Saved" : "Save", 
                  systemImage: isSaved ? "heart.fill" : "heart")
                .font(.headline)
        }
        .buttonStyle(.bordered)
        .foregroundColor(isSaved ? .red : .primary)
        .accessibilityLabel(isSaved ? "Remove from favorites" : "Add to favorites")
        .accessibilityHint(isSaved ? "Remove this analysis from your favorites" : "Save this analysis to your favorites")
    }
    
    private func saveAction() {
        isSaved.toggle()
        // Save implementation
    }
}
```

## Accessible Data Entry with Validation
```swift
struct AccessibleProductEntryForm: View {
    @StateObject private var viewModel = ProductEntryViewModel()
    @FocusState private var focusedField: Field?
    
    enum Field: CaseIterable {
        case productName, brand, condition, price
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    TextField("Product Name", text: $viewModel.productName)
                        .focused($focusedField, equals: .productName)
                        .accessibilityLabel("Product name")
                        .accessibilityHint("Enter the full name of your product")
                        .submitLabel(.next)
                        .onSubmit {
                            focusedField = .brand
                        }
                    
                    if !viewModel.productNameError.isEmpty {
                        Text(viewModel.productNameError)
                            .font(.caption)
                            .foregroundColor(.red)
                            .accessibilityLabel("Error: \\(viewModel.productNameError)")
                    }
                    
                    TextField("Brand", text: $viewModel.brand)
                        .focused($focusedField, equals: .brand)
                        .accessibilityLabel("Product brand")
                        .accessibilityHint("Enter the brand or manufacturer")
                        .submitLabel(.next)
                        .onSubmit {
                            focusedField = .condition
                        }
                    
                    Picker("Condition", selection: $viewModel.condition) {
                        ForEach(ProductCondition.allCases, id: \\.self) { condition in
                            Text(condition.displayName)
                                .tag(condition)
                        }
                    }
                    .focused($focusedField, equals: .condition)
                    .accessibilityLabel("Product condition")
                    .accessibilityHint("Select the current condition of your product")
                    
                    TextField("Purchase Price", value: $viewModel.purchasePrice, format: .currency(code: "USD"))
                        .focused($focusedField, equals: .price)
                        .keyboardType(.decimalPad)
                        .accessibilityLabel("Purchase price")
                        .accessibilityHint("Enter the original purchase price")
                        .submitLabel(.done)
                        .onSubmit {
                            focusedField = nil
                            submitForm()
                        }
                    
                    if !viewModel.priceError.isEmpty {
                        Text(viewModel.priceError)
                            .font(.caption)
                            .foregroundColor(.red)
                            .accessibilityLabel("Error: \\(viewModel.priceError)")
                    }
                } header: {
                    Text("Product Information")
                } footer: {
                    Text("All fields are required for accurate analysis")
                        .accessibilityHint("Complete all fields to proceed with analysis")
                }
                
                Section {
                    Button("Analyze Product") {
                        submitForm()
                    }
                    .frame(maxWidth: .infinity)
                    .disabled(!viewModel.isFormValid)
                    .accessibilityLabel("Analyze product")
                    .accessibilityHint(viewModel.isFormValid ? "Submit form for analysis" : "Complete all required fields first")
                }
            }
            .navigationTitle("Add Product")
            .navigationBarTitleDisplayMode(.large)
            .alert("Form Error", isPresented: $viewModel.showingError) {
                Button("OK") {
                    // Focus on first error field
                    if !viewModel.productNameError.isEmpty {
                        focusedField = .productName
                    } else if !viewModel.priceError.isEmpty {
                        focusedField = .price
                    }
                }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }
    
    private func submitForm() {
        viewModel.validateAndSubmit()
    }
}
```
                """,
                "target_framework": "swift_ios",
                "wcag_level": "AA",
                "category": "forms",
                "source": "iOS Accessibility Guidelines Level AA"
            },
            
            # React - WCAG AA Level
            {
                "content": """
# React WCAG Level AA Accessibility Patterns

## Accessible Form Components with ARIA
```jsx
import React, { useState, useRef, useEffect } from 'react';
import { validateForm, uploadImage, analyzeProduct } from '../services/api';

const AccessibleProductForm = () => {
  const [formData, setFormData] = useState({
    productName: '',
    condition: '',
    brand: '',
    purchasePrice: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');
  
  const firstErrorRef = useRef(null);
  const announcementRef = useRef(null);
  
  // Focus management for errors
  useEffect(() => {
    if (Object.keys(errors).length > 0 && firstErrorRef.current) {
      firstErrorRef.current.focus();
    }
  }, [errors]);
  
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitMessage('');
    
    // Validate form
    const validationErrors = validateForm(formData);
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setIsSubmitting(false);
      
      // Announce errors to screen readers
      const errorCount = Object.keys(validationErrors).length;
      setSubmitMessage(`Form has ${errorCount} ${errorCount === 1 ? 'error' : 'errors'}. Please review and correct.`);
      return;
    }
    
    try {
      const result = await analyzeProduct(formData);
      setSubmitMessage(`Analysis completed successfully. Estimated value: $${result.estimatedValue}`);
      
      // Reset form on success
      setFormData({
        productName: '',
        condition: '',
        brand: '',
        purchasePrice: ''
      });
      
    } catch (error) {
      setSubmitMessage('Analysis failed. Please try again.');
      console.error('Analysis error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} noValidate className="accessible-form">
      {/* Screen reader announcements */}
      <div 
        ref={announcementRef}
        aria-live="polite" 
        aria-atomic="true"
        className="sr-only"
      >
        {submitMessage}
      </div>
      
      <fieldset className="form-section">
        <legend className="form-legend">Product Information</legend>
        
        {/* Product Name Field */}
        <div className="form-group">
          <label 
            htmlFor="productName" 
            className={`form-label ${errors.productName ? 'error' : ''}`}
          >
            Product Name *
          </label>
          <input
            ref={errors.productName ? firstErrorRef : null}
            type="text"
            id="productName"
            value={formData.productName}
            onChange={(e) => handleInputChange('productName', e.target.value)}
            aria-required="true"
            aria-invalid={!!errors.productName}
            aria-describedby={`productName-help ${errors.productName ? 'productName-error' : ''}`}
            className={`form-input ${errors.productName ? 'input-error' : ''}`}
            autoComplete="off"
          />
          <div id="productName-help" className="help-text">
            Enter the full product name including brand and model
          </div>
          {errors.productName && (
            <div 
              id="productName-error" 
              className="error-message"
              role="alert"
              aria-live="polite"
            >
              {errors.productName}
            </div>
          )}
        </div>
        
        {/* Brand Field */}
        <div className="form-group">
          <label 
            htmlFor="brand" 
            className={`form-label ${errors.brand ? 'error' : ''}`}
          >
            Brand *
          </label>
          <input
            type="text"
            id="brand"
            value={formData.brand}
            onChange={(e) => handleInputChange('brand', e.target.value)}
            aria-required="true"
            aria-invalid={!!errors.brand}
            aria-describedby={`brand-help ${errors.brand ? 'brand-error' : ''}`}
            className={`form-input ${errors.brand ? 'input-error' : ''}`}
            list="popular-brands"
          />
          <datalist id="popular-brands">
            <option value="Nike" />
            <option value="Adidas" />
            <option value="Apple" />
            <option value="Samsung" />
            <option value="Sony" />
          </datalist>
          <div id="brand-help" className="help-text">
            Select or enter the product brand
          </div>
          {errors.brand && (
            <div 
              id="brand-error" 
              className="error-message"
              role="alert"
            >
              {errors.brand}
            </div>
          )}
        </div>
        
        {/* Condition Field */}
        <div className="form-group">
          <label 
            htmlFor="condition" 
            className={`form-label ${errors.condition ? 'error' : ''}`}
          >
            Condition *
          </label>
          <select
            id="condition"
            value={formData.condition}
            onChange={(e) => handleInputChange('condition', e.target.value)}
            aria-required="true"
            aria-invalid={!!errors.condition}
            aria-describedby={`condition-help ${errors.condition ? 'condition-error' : ''}`}
            className={`form-select ${errors.condition ? 'input-error' : ''}`}
          >
            <option value="">Select condition</option>
            <option value="new">New with tags/box</option>
            <option value="like-new">Like new</option>
            <option value="good">Good condition</option>
            <option value="fair">Fair condition</option>
            <option value="poor">Poor condition</option>
          </select>
          <div id="condition-help" className="help-text">
            Choose the condition that best describes your item
          </div>
          {errors.condition && (
            <div 
              id="condition-error" 
              className="error-message"
              role="alert"
            >
              {errors.condition}
            </div>
          )}
        </div>
        
        {/* Purchase Price Field */}
        <div className="form-group">
          <label 
            htmlFor="purchasePrice" 
            className={`form-label ${errors.purchasePrice ? 'error' : ''}`}
          >
            Original Purchase Price *
          </label>
          <div className="input-wrapper">
            <span className="currency-symbol" aria-hidden="true">$</span>
            <input
              type="number"
              id="purchasePrice"
              value={formData.purchasePrice}
              onChange={(e) => handleInputChange('purchasePrice', e.target.value)}
              aria-required="true"
              aria-invalid={!!errors.purchasePrice}
              aria-describedby={`purchasePrice-help ${errors.purchasePrice ? 'purchasePrice-error' : ''}`}
              className={`form-input currency-input ${errors.purchasePrice ? 'input-error' : ''}`}
              min="0"
              step="0.01"
              placeholder="0.00"
            />
          </div>
          <div id="purchasePrice-help" className="help-text">
            Enter the amount you originally paid for this item
          </div>
          {errors.purchasePrice && (
            <div 
              id="purchasePrice-error" 
              className="error-message"
              role="alert"
            >
              {errors.purchasePrice}
            </div>
          )}
        </div>
      </fieldset>
      
      {/* Submit Button */}
      <div className="form-actions">
        <button
          type="submit"
          disabled={isSubmitting}
          className="submit-button"
          aria-describedby="submit-help"
        >
          {isSubmitting ? (
            <>
              <span className="spinner" aria-hidden="true"></span>
              Analyzing...
            </>
          ) : (
            'Analyze Product'
          )}
        </button>
        <div id="submit-help" className="help-text">
          Click to start AI-powered value analysis
        </div>
      </div>
    </form>
  );
};

export default AccessibleProductForm;
```

## Accessible Data Display Components
```jsx
import React, { useState } from 'react';

const AccessibleAnalysisResults = ({ analysisData, onShare, onSave }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  
  const handleSave = async () => {
    try {
      await onSave(analysisData);
      setIsSaved(true);
      // Announce success to screen reader
      announceToScreenReader('Analysis saved to favorites');
    } catch (error) {
      announceToScreenReader('Failed to save analysis');
    }
  };
  
  const announceToScreenReader = (message) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };
  
  const getConfidenceLevel = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };
  
  return (
    <article 
      className="analysis-results"
      role="main"
      aria-labelledby="results-title"
    >
      <header className="results-header">
        <h1 id="results-title" className="results-title">
          Analysis Results
        </h1>
        <p className="results-subtitle">
          AI-powered valuation for {analysisData.productName}
        </p>
      </header>
      
      <div className="results-content">
        {/* Product Image */}
        <div className="product-image-container">
          <img
            src={analysisData.imageUrl}
            alt={analysisData.imageDescription}
            className="product-image"
            loading="lazy"
          />
          <div className="image-caption sr-only">
            {analysisData.detailedImageDescription}
          </div>
        </div>
        
        {/* Key Results */}
        <section className="key-results" aria-labelledby="key-results-title">
          <h2 id="key-results-title" className="section-title">
            Valuation Summary
          </h2>
          
          <div className="value-display">
            <div className="estimated-value">
              <span className="value-label">Estimated Current Value:</span>
              <span 
                className="value-amount"
                aria-label={`Estimated value: ${formatCurrency(analysisData.estimatedValue)}`}
              >
                {formatCurrency(analysisData.estimatedValue)}
              </span>
            </div>
            
            <div className="value-change">
              <span className="change-label">Change from Purchase:</span>
              <span 
                className={`change-amount ${analysisData.valueChange >= 0 ? 'positive' : 'negative'}`}
                aria-label={`Value change: ${analysisData.valueChange >= 0 ? 'increased' : 'decreased'} by ${formatCurrency(Math.abs(analysisData.valueChange))}`}
              >
                {analysisData.valueChange >= 0 ? '+' : ''}
                {formatCurrency(analysisData.valueChange)}
              </span>
            </div>
          </div>
          
          {/* Confidence Indicator */}
          <div className="confidence-indicator">
            <span className="confidence-label">Analysis Confidence:</span>
            <div 
              className="confidence-bar"
              role="progressbar"
              aria-valuenow={Math.round(analysisData.confidence * 100)}
              aria-valuemin="0"
              aria-valuemax="100"
              aria-label={`Confidence level: ${getConfidenceLevel(analysisData.confidence)} (${Math.round(analysisData.confidence * 100)}%)`}
            >
              <div 
                className="confidence-fill"
                style={{ width: `${analysisData.confidence * 100}%` }}
              ></div>
            </div>
            <span className="confidence-text">
              {getConfidenceLevel(analysisData.confidence)} 
              ({Math.round(analysisData.confidence * 100)}%)
            </span>
          </div>
        </section>
        
        {/* Detailed Analysis */}
        <section className="detailed-analysis" aria-labelledby="details-title">
          <h2 id="details-title" className="section-title">
            Analysis Details
          </h2>
          
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-controls="analysis-details"
            className="details-toggle"
          >
            {isExpanded ? 'Hide' : 'Show'} Analysis Details
            <span className="toggle-icon" aria-hidden="true">
              {isExpanded ? '−' : '+'}
            </span>
          </button>
          
          <div 
            id="analysis-details"
            className={`details-content ${isExpanded ? 'expanded' : 'collapsed'}`}
            aria-hidden={!isExpanded}
          >
            <dl className="analysis-facts">
              {analysisData.details.map((detail, index) => (
                <div key={index} className="fact-item">
                  <dt className="fact-label">{detail.label}:</dt>
                  <dd className="fact-value">{detail.value}</dd>
                </div>
              ))}
            </dl>
            
            {analysisData.marketTrends && (
              <div className="market-trends">
                <h3 className="trends-title">Market Trends</h3>
                <p className="trends-description">
                  {analysisData.marketTrends}
                </p>
              </div>
            )}
          </div>
        </section>
        
        {/* Action Buttons */}
        <div className="results-actions" role="group" aria-label="Analysis actions">
          <button
            type="button"
            onClick={onShare}
            className="action-button share-button"
            aria-describedby="share-help"
          >
            <span className="button-icon" aria-hidden="true">📤</span>
            Share Analysis
          </button>
          <div id="share-help" className="sr-only">
            Share this analysis with others via email or social media
          </div>
          
          <button
            type="button"
            onClick={handleSave}
            className={`action-button save-button ${isSaved ? 'saved' : ''}`}
            aria-describedby="save-help"
            disabled={isSaved}
          >
            <span className="button-icon" aria-hidden="true">
              {isSaved ? '❤️' : '🤍'}
            </span>
            {isSaved ? 'Saved' : 'Save to Favorites'}
          </button>
          <div id="save-help" className="sr-only">
            {isSaved 
              ? 'This analysis has been saved to your favorites'
              : 'Save this analysis to your favorites for quick access later'
            }
          </div>
        </div>
      </div>
    </article>
  );
};

export default AccessibleAnalysisResults;
```
                """,
                "target_framework": "react",
                "wcag_level": "AA",
                "category": "components",
                "source": "React Accessibility Guidelines Level AA"
            }
        ]
        
        # Add each pattern
        print(f"Adding {len(patterns)} comprehensive accessibility patterns...")
        
        for i, pattern in enumerate(patterns):
            print(f"\n📝 Adding pattern {i+1}/{len(patterns)}: {pattern['target_framework']} - {pattern['category']} (WCAG {pattern['wcag_level']})")
            
            try:
                result = add_pattern_direct(
                    pattern_content=pattern["content"],
                    target_framework=pattern["target_framework"],
                    wcag_level=pattern["wcag_level"],
                    category=pattern["category"],
                    source=pattern["source"]
                )
                print(f"   {result}")
            except Exception as e:
                print(f"   ❌ Failed to add pattern: {str(e)[:100]}")
        
        # Show final statistics
        data = collection.get()
        total_docs = len(data["ids"])
        
        frameworks = {}
        wcag_levels = {}
        categories = {}
        
        for metadata in data["metadatas"]:
            if metadata.get("framework") == "accessibility":
                fw = metadata.get("target_framework", "unknown")
                level = metadata.get("wcag_level", "unknown")
                cat = metadata.get("category", "unknown")
                
                frameworks[fw] = frameworks.get(fw, 0) + 1
                wcag_levels[level] = wcag_levels.get(level, 0) + 1
                categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n✅ Successfully populated comprehensive accessibility patterns!")
        print(f"\n📊 Final Database Statistics:")
        print(f"   Total Documents: {total_docs}")
        print(f"   Accessibility Patterns: {sum(frameworks.values())}")
        
        print(f"\n🎯 By Framework:")
        for fw, count in sorted(frameworks.items()):
            print(f"   • {fw}: {count} patterns")
        
        print(f"\n📋 By WCAG Level:")
        for level, count in sorted(wcag_levels.items()):
            print(f"   • Level {level}: {count} patterns")
        
        print(f"\n🏷️  By Category:")
        for cat, count in sorted(categories.items()):
            print(f"   • {cat}: {count} patterns")
        
        print(f"\n🔍 Search Examples:")
        print("   - search_accessibility_patterns('form validation')")
        print("   - search_accessibility_patterns('VoiceOver', framework='swift_ios')")  
        print("   - search_accessibility_patterns('ARIA', wcag_level='AA')")
        print("   - search_accessibility_patterns('React components', framework='react')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating comprehensive patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    populate_comprehensive_accessibility_patterns()