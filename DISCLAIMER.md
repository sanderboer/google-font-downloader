# Automation System Disclaimer

## Font Coverage Limitations

The automated Google Fonts catalog generation system provides comprehensive coverage but **does not guarantee absolute parity** with fonts.google.com. Here's what users should understand:

### ⚠️ Key Limitations

#### **API Restrictions**
Google's CSS2 API actively blocks automated requests, which means:
- Variant detection relies on fallback mechanisms
- Some fonts may show fewer weight options than actually available
- New Google API restrictions could affect future catalog accuracy

#### **Timing Differences**
- New fonts may appear on fonts.google.com before our weekly GitHub repository scan
- Google can modify font availability instantly, while our system updates weekly
- Emergency font removals may not be reflected immediately

#### **Regional & Subset Variations**
- Google may serve different font subsets based on user location
- Character set availability (Latin, Cyrillic, Arabic, etc.) may vary
- License restrictions in certain regions are not automatically detected

#### **Technical Dependencies**
- Relies on GitHub's mirror of Google Fonts repository
- Subject to GitHub API rate limits and availability
- METADATA.pb parsing may not capture all edge cases

### ✅ What This System Provides

#### **Best-Effort Completeness**
- Processes all fonts available in Google's official repository
- Uses multiple data sources (GitHub, METADATA.pb, CSS2 fallbacks)
- Provides comprehensive variant lists when APIs cooperate

#### **Reliable Operation**
- Graceful degradation when APIs are blocked
- Fallback mechanisms ensure fonts are still accessible
- Weekly updates maintain reasonable currency

#### **Quality Assurance**
- Automated validation of catalog structure
- Popular fonts coverage verification  
- Change detection prevents broken updates

### 🎯 Recommended Usage

#### **Primary Use Cases** ✅
- **Offline development environments**
- **CI/CD pipelines** requiring font consistency
- **Fallback catalogs** when Google APIs are blocked
- **Bulk font processing** projects

#### **Verify Separately** ⚠️
- **Production applications**: Always verify critical fonts on fonts.google.com
- **Commercial projects**: Check licensing and availability directly with Google
- **Precise variant requirements**: Cross-reference with Google's official CSS2 API
- **International deployments**: Test font availability in target regions

### 🔄 Continuous Improvement

We continuously work to improve accuracy by:
- Monitoring Google's API changes and adapting accordingly
- Implementing multiple fallback strategies
- Providing transparent logging of limitations and failures
- Accepting community feedback and bug reports

### 📞 Support

If you encounter specific fonts that are:
- Available on fonts.google.com but missing from our catalog
- Showing incorrect variants or metadata
- Causing integration issues

Please report these as GitHub issues with:
1. Font name and expected variants
2. Comparison with fonts.google.com
3. Your use case and requirements

---

**Remember**: This automation system is designed to provide excellent Google Fonts coverage while working within the constraints of automated API access. For mission-critical applications, always verify font availability through official Google channels.