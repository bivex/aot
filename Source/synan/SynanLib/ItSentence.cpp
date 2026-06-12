#include "ItSentence.h"
#include "ItSyntaxOpt.h"
#include "ItFormatCaller.h"

CItSentence::CItSentence(const CSyntaxOpt* opt) : CSentence(opt)
{
}

CItSentence::~CItSentence()
{
}

void CItSentence::ReadNextFromPlmLinesLanguageSpecific()
{
}

void CItSentence::BuildSubjAndPredRelation(CMorphVariant& synVariant, long RootWordNo, EClauseType ClauseType)
{
	synVariant.ResetSubj();

	long iPred = RootWordNo;
	if (iPred >= 0 && iPred < (long)synVariant.m_SynUnits.size()) {
		const CSynUnit& PU = synVariant.m_SynUnits[iPred];
		const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
		if (!PW.m_Homonyms.empty() && PU.m_iHomonymNum < (int)PW.m_Homonyms.size()) {
			const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];
			if (!GetItGramTab()->is_verb_form(PH.m_iPoses)) {
				iPred = -1;
			}
		}
	}

	if (iPred == -1 || iPred >= (long)synVariant.m_SynUnits.size()) {
		for (long i = 0; i < (long)synVariant.m_SynUnits.size(); i++) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;
			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];
			if (GetItGramTab()->is_verb_form(H.m_iPoses)) {
				iPred = i;
				break;
			}
		}
	}

	if (iPred == -1 || iPred >= (long)synVariant.m_SynUnits.size()) return;
	synVariant.m_iPredk = iPred;

	const CSynUnit& PU = synVariant.m_SynUnits[iPred];
	const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
	if (PW.m_Homonyms.empty() || PU.m_iHomonymNum >= (int)PW.m_Homonyms.size()) return;
	const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];

	// Italian SVO — scan backward from predicate for subject
	for (long i = iPred - 1; i >= 0; i--) {
		const CSynUnit& U = synVariant.m_SynUnits[i];
		if (U.m_Type != EWord) continue;

		const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
		if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
		const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

		if (GetItGramTab()->IsMorphNoun(H.m_iPoses) ||
		    GetItGramTab()->is_morph_pronoun(H.m_iPoses)) {

			if (GetItGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
				synVariant.m_Subjects.push_back(i);
				synVariant.m_bGoodSubject = true;
				break;
			}
		}
	}

	// Italian allows inverted word order — forward scan after verb
	if (!synVariant.m_bGoodSubject) {
		for (long i = iPred + 1; i < (long)synVariant.m_SynUnits.size(); i++) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;

			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			if (W.m_Homonyms.empty() || U.m_iHomonymNum >= (int)W.m_Homonyms.size()) continue;
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

			if (GetItGramTab()->IsMorphNoun(H.m_iPoses) ||
			    GetItGramTab()->is_morph_pronoun(H.m_iPoses)) {

				if (GetItGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
					synVariant.m_Subjects.push_back(i);
					synVariant.m_bGoodSubject = true;
					break;
				}
			}
		}
	}
}

int CItSentence::GetCountOfStrongRoots(const CClause& C, const CMorphVariant& synVar) const
{
	return 1;
}

bool CItSentence::WordSchemeEqForThesaurus(const CSynHomonym& Homonym, const CSynPlmLine& word_scheme) const
{
	return false;
}

bool CItSentence::RunSyntaxInClauses(ESynRulesSet type)
{
	try {
		if (m_pSyntaxOptions == NULL) return false;
		int count = GetClausesCount();
		for (int i = 0; i < count; i++) {
			BuildGLRGroupsInClause(GetClause(i));
		}
		return true;
	}
	catch (...) {
		return false;
	}
}

void CItSentence::AfterBuildGroupsTrigger(CClause& C)
{
}

CFormatCaller* CItSentence::GetNewFormatCaller() const
{
	return new CItFormatCaller(GetOpt());
}

bool CItSentence::BuildClauses()
{
	m_bPanicMode = IsPanicSentence();
	assert(GetClausesCount() == 0);
	FindGraPairs();

	if (!BuildInitialClauses()) {
		return false;
	}

	RunSyntaxInClauses(AllRules);
	AssignClauseNoToWords();
	return true;
}

void CItSentence::InitHomonymMorphInfo(CSynHomonym& H)
{
	H.InitAncodePattern();
}

void CItSentence::InitHomonymLanguageSpecific(CSynHomonym& H, const CLemWord* pWord)
{
}

void CItSentence::SolveAmbiguityUsingRuleForTwoPredicates(int iFirstWord, int iLastWord)
{
}

void CItSentence::ChooseClauseType(const std::vector<SClauseType>& vectorTypes, CMorphVariant& V)
{
	V.m_ClauseTypeNo = 0;
}

bool CItSentence::SetClauseBorderIfThereAreTwoPotentialPredicates(int FWrd, int LWrd)
{
	return false;
}

bool CItSentence::IsInitialClauseType(EClauseType ClauseType) const
{
	return true;
}

bool CItSentence::IsRelativSentencePronoun(int ClauseStartWordNo, int WordNo, int& HomonymNo) const
{
	return false;
}

bool CItSentence::AllHomonymsArePredicates(const CSynWord& W) const
{
	for (size_t i = 0; i < W.m_Homonyms.size(); i++) {
		if (!GetItGramTab()->is_verb_form(W.m_Homonyms[i].m_iPoses))
			return false;
	}
	return !W.m_Homonyms.empty();
}

bool CItSentence::CanBeRelativeAntecedent(const CSynHomonym& H) const
{
	return GetItGramTab()->IsMorphNoun(H.m_iPoses);
}

bool CItSentence::IsProfession(const CSynHomonym& H) const
{
	return false;
}

EClauseType CItSentence::GetClauseTypeByAncodePattern(const CAncodePattern& Pattern) const
{
	return (EClauseType)0;
}
