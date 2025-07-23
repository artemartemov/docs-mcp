#!/usr/bin/env python3
"""
Direct population of accessibility patterns in Chroma database
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

def populate_accessibility_patterns():
    """Add comprehensive accessibility patterns to the database"""
    
    print("🔧 Populating Accessibility Patterns Database")
    print("=" * 60)
    
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
                "added_at": datetime.utcnow().isoformat(),
                "content_hash": hashlib.md5(pattern_content.encode()).hexdigest()
            }
            
            collection.add(
                documents=[pattern_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return f"✅ Added accessibility pattern for {target_framework} (WCAG {wcag_level})"
        
        # Accessibility patterns to add
        patterns = [
            {
                "content": """
# FastAPI Accessibility Patterns

## Form Validation with ARIA
```python
from fastapi import Form, HTTPException
from pydantic import BaseModel, Field

class AccessibleFormData(BaseModel):
    email: str = Field(
        ..., 
        description="Email address for account access",
        json_schema_extra={
            "aria_label": "Enter your email address",
            "aria_describedby": "email-help",
            "aria_required": "true"
        }
    )
    
@app.post("/submit-form")
async def submit_accessible_form(
    email: str = Form(..., description="Email address")
):
    # Server-side validation with descriptive errors
    if not email or "@" not in email:
        raise HTTPException(
            status_code=422,
            detail={
                "field": "email",
                "message": "Please enter a valid email address",
                "aria_live": "polite"
            }
        )
```

## API Documentation Accessibility
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="ResaleAnalyzer API",
        version="1.0.0",
        description="Accessible API for image analysis and resale value estimation",
        routes=app.routes,
    )
    
    # Add accessibility metadata
    openapi_schema["info"]["x-accessibility"] = {
        "wcag_level": "AA",
        "screen_reader_compatible": True,
        "keyboard_navigation": True
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```
                """,
                "target_framework": "fastapi",
                "wcag_level": "AA",
                "category": "forms",
                "source": "ResaleAnalyzer patterns"
            },
            {
                "content": """
# Swift iOS Accessibility Patterns

## VoiceOver Support for Image Analysis
```swift
struct AnalysisResultView: View {
    let analysisResult: AnalysisResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Accessible image display
            AsyncImage(url: analysisResult.imageURL) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fit)
            } placeholder: {
                ProgressView()
                    .accessibilityLabel("Loading product image")
            }
            .accessibilityLabel(analysisResult.imageDescription)
            .accessibilityAddTraits(.isImage)
            .accessibilityRemoveTraits(.isButton)
            
            // Accessible results display
            VStack(alignment: .leading, spacing: 8) {
                Text("Analysis Results")
                    .font(.headline)
                    .accessibilityAddTraits(.isHeader)
                
                ForEach(analysisResult.details, id: \\.id) { detail in
                    HStack {
                        Text(detail.label)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Text(detail.value)
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    .accessibilityElement(children: .combine)
                    .accessibilityLabel("\\(detail.label): \\(detail.value)")
                }
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Product analysis results for \\(analysisResult.productName)")
    }
}
```

## Dynamic Type Support
```swift
extension View {
    func adaptiveFont(_ style: Font.TextStyle) -> some View {
        self.font(.system(style, design: .default))
            .dynamicTypeSize(.xSmall ... .accessibility5)
    }
}

struct AccessibleAnalysisCard: View {
    var body: some View {
        VStack(alignment: .leading) {
            Text("Product Value")
                .adaptiveFont(.headline)
                .accessibilityAddTraits(.isHeader)
            
            Text("$124.99")
                .adaptiveFont(.title2)
                .accessibilityLabel("Estimated value: 124 dollars and 99 cents")
        }
        .padding()
        .background(Color(.systemGroupedBackground))
        .cornerRadius(12)
        .accessibilityElement(children: .combine)
    }
}
```
                """,
                "target_framework": "swift_ios",
                "wcag_level": "AA",
                "category": "mobile",
                "source": "ResaleAnalyzer iOS patterns"
            },
            {
                "content": """
# Web Accessibility Patterns

## Image Alt Text Best Practices
```html
<!-- For functional images -->
<img src="product.jpg" 
     alt="Nike Air Max sneakers in white and blue colorway, size 10, showing minor wear on sole"
     role="img">

<!-- For decorative images -->
<img src="background-pattern.jpg" 
     alt="" 
     role="presentation">

<!-- For complex images with data -->
<figure>
    <img src="price-chart.jpg" 
         alt="Price trend chart showing value increase from $50 to $120 over 6 months">
    <figcaption>
        Detailed price history: 
        <a href="#price-data">View tabular data</a>
    </figcaption>
</figure>
```

## Form Labels and Error Handling
```html
<form>
    <div class="form-group">
        <label for="product-condition" class="required">
            Product Condition
        </label>
        <select id="product-condition" 
                aria-describedby="condition-help condition-error"
                aria-required="true"
                aria-invalid="false">
            <option value="">Select condition</option>
            <option value="new">New with tags</option>
            <option value="like-new">Like new</option>
            <option value="good">Good condition</option>
        </select>
        <div id="condition-help" class="help-text">
            Choose the condition that best describes your item
        </div>
        <div id="condition-error" class="error-text" aria-live="polite">
            <!-- Error messages appear here -->
        </div>
    </div>
</form>
```

## Color Contrast Requirements
```css
:root {
    /* WCAG AA compliant color palette */
    --primary-color: #1a365d;      /* 7.23:1 contrast ratio */
    --secondary-color: #2d3748;    /* 6.12:1 contrast ratio */
    --success-color: #22543d;      /* 5.74:1 contrast ratio */
    --error-color: #742a2a;       /* 5.12:1 contrast ratio */
    --text-color: #1a202c;        /* 16.75:1 contrast ratio */
    --background-color: #ffffff;
}

.button-primary {
    background-color: var(--primary-color);
    color: var(--background-color);
    /* Minimum 4.5:1 contrast ratio for normal text */
    /* Minimum 3:1 contrast ratio for large text */
}

/* Focus indicators */
.focusable:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}
```
                """,
                "target_framework": "web",
                "wcag_level": "AA", 
                "category": "general",
                "source": "WCAG 2.2 guidelines"
            }
        ]
        
        # Add each pattern
        for i, pattern in enumerate(patterns):
            print(f"\n📝 Adding pattern {i+1}/{len(patterns)}: {pattern['target_framework']} - {pattern['category']}")
            
            result = add_pattern_direct(
                pattern_content=pattern["content"],
                target_framework=pattern["target_framework"],
                wcag_level=pattern["wcag_level"],
                category=pattern["category"],
                source=pattern["source"]
            )
            
            print(f"   {result}")
        
        print(f"\n✅ Successfully populated {len(patterns)} accessibility patterns!")
        print("\n🔍 You can now search these patterns using:")
        print("   - search_accessibility_patterns('form validation')")
        print("   - search_accessibility_patterns('VoiceOver', framework='swift_ios')")  
        print("   - search_accessibility_patterns('color contrast', wcag_level='AA')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    populate_accessibility_patterns()